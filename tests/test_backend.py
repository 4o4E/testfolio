import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from io import BytesIO
from urllib.request import urlopen

from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image
import pytest
import uvicorn

from backend import app as backend_app

ROOT = Path(__file__).resolve().parents[1]


def test_real_sqlite_http_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(backend_app, "DATA_DIR", tmp_path / "db")
    monkeypatch.setattr(backend_app, "ARTIFACT_DIR", tmp_path / "artifacts")
    monkeypatch.setenv("TEST_RESULTS_WRITE_TOKEN", "integration-secret")
    reader = TestClient(backend_app.create_read_app())
    writer = TestClient(backend_app.create_write_app())
    auth = {"Authorization": "Bearer integration-secret"}
    case = {
        "id": "case-1", "project_id": "project-1", "title": "Login", "path": ["Auth", "Login"],
        "requirement": "User can log in", "preconditions": [],
        "steps": [{"action": "submit", "expected": "dashboard"}], "priority": "P1", "tags": [], "source": "manual",
    }
    catalog = {"project": {"id": "project-1", "title": "Sample", "description": "desc"}, "cases": [case]}
    assert writer.put("/write/catalog", json=catalog, headers=auth).status_code == 200
    assert reader.get("/api/projects").json()[0]["case_count"] == 1
    assert reader.post("/write/runs", json={}).status_code == 404
    empty_scope = {"id": "empty-run", "project_id": "project-1", "title": "Empty", "environment": "local", "kind": "browser", "started_at": "2026-10-26T10:00:00Z", "versions": {}, "scope_case_ids": [], "summary": "", "source": "manual"}
    assert writer.post("/write/runs", json=empty_scope, headers=auth).status_code == 422
    invalid_case = {**case, "path": [], "steps": []}
    assert writer.put("/write/catalog", json={**catalog, "cases": [invalid_case]}, headers=auth).status_code == 422
    image_buffer = BytesIO()
    Image.new("RGB", (2, 2), "white").save(image_buffer, format="PNG")
    png = image_buffer.getvalue()
    uploaded = writer.post("/write/artifacts", files={"file": ("proof.png", png, "image/png")}, headers=auth)
    assert uploaded.status_code == 200
    artifact_id = uploaded.json()["artifact_id"]
    assert reader.get(uploaded.json()["url"]).content == png
    assert writer.post("/write/artifacts", files={"file": ("invalid.png", b"not a PNG", "image/png")}, headers=auth).status_code == 415
    run = {
        "id": "run-1", "project_id": "project-1", "title": "Round 1", "environment": "local", "kind": "browser",
        "started_at": "2026-10-26T10:00:00Z", "versions": {}, "scope_case_ids": ["case-1"], "summary": "", "source": "manual",
    }
    assert writer.post("/write/runs", json=run, headers=auth).status_code == 200
    other_case = {**case, "project_id": "project-2", "title": "Project two login"}
    other_catalog = {"project": {"id": "project-2", "title": "Other", "description": "separate project"}, "cases": [other_case]}
    assert writer.put("/write/catalog", json=other_catalog, headers=auth).status_code == 200
    other_run = {**run, "id": "run-2", "project_id": "project-2"}
    assert writer.post("/write/runs", json=other_run, headers=auth).status_code == 200
    assert reader.get("/api/projects/project-1/cases/" + case["id"]).json()["history"][0]["run"]["id"] == "run-1"
    assert reader.get("/api/projects/project-2/cases/" + case["id"]).json()["history"][0]["run"]["id"] == "run-2"
    assert [item["title"] for item in reader.get("/api/projects/project-1/cases").json()] == ["Login"]
    assert [item["title"] for item in reader.get("/api/projects/project-2/cases").json()] == ["Project two login"]
    changed_case = {**case, "title": "Changed after snapshot"}
    assert writer.put("/write/catalog", json={**catalog, "cases": [changed_case]}, headers=auth).status_code == 200
    result = {
        "case_id": "case-1", "status": "passed", "actual": "Dashboard displayed", "steps": [],
        "evidence": [{"artifact_id": artifact_id, "caption": "screen", "marks": [{"x": 1, "y": 2, "w": 3, "h": 4, "label": 1}], "crop": {"x": 0, "y": 0, "w": 10, "h": 10}}],
        "issues": [], "recorded_at": "2026-10-26T10:01:00Z", "notes": "",
    }
    endpoint = "/write/runs/run-1/results"
    assert writer.post(endpoint, json=result, headers=auth).status_code == 200
    assert writer.post(endpoint, json=result, headers=auth).status_code == 200
    conflicting = {**result, "actual": "A different observation"}
    assert writer.post(endpoint, json=conflicting, headers=auth).status_code == 409
    run_detail = reader.get("/api/runs/run-1").json()
    assert run_detail["cases"][0]["case"]["title"] == "Login"
    assert run_detail["counts"]["passed"] == 1
    finish = writer.post("/write/runs/run-1/finish", json={"state": "completed", "summary": "done"}, headers=auth)
    assert finish.status_code == 200
    assert writer.post("/write/runs/run-1/results", json={**result, "case_id": "case-1", "actual": "late"}, headers=auth).status_code == 409


def test_static_entry_paths_and_unknown_paths(tmp_path, monkeypatch):
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<!doctype html><title>app</title>")
    (static / "assets" / "app.js").write_text("window.ready = true")
    monkeypatch.chdir(tmp_path)
    client = TestClient(backend_app.create_read_app())
    paths = ["/", "/projects", "/projects/project-1", "/projects/project-1/runs/run-1", "/projects/project-1/runs/run-1/cases/case-1"]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200
        assert response.text == "<!doctype html><title>app</title>"
    assert client.get("/assets/app.js").text == "window.ready = true"
    assert client.get("/not-a-page").status_code == 404
    assert client.get("/api/not-a-route").status_code == 404
    assert client.get("/artifacts/missing").status_code == 404


def test_setup_local_preserves_credentials_and_secure_modes(tmp_path):
    script = ROOT / "scripts/setup_local.py"
    config_dir = tmp_path / "private"
    first = subprocess.run([sys.executable, str(script), "--config-dir", str(config_dir), "--read-url", "http://reader.test:8080", "--write-url", "http://writer.test:8081"], capture_output=True, text=True, check=True)
    config_path = config_dir / "client.json"
    config = json.loads(config_path.read_text())
    token = config["token"]
    assert token not in first.stdout + first.stderr
    assert config_dir.stat().st_mode & 0o777 == 0o700
    assert config_path.stat().st_mode & 0o777 == 0o600
    subprocess.run([sys.executable, str(script), "--config-dir", str(config_dir)], capture_output=True, text=True, check=True)
    repeated = json.loads(config_path.read_text())
    assert repeated["token"] == token
    assert repeated["read_url"] == "http://reader.test:8080"
    assert repeated["write_url"] == "http://writer.test:8081"
    assert (config_dir / "server.env").stat().st_mode & 0o777 == 0o600
    invalid = subprocess.run([sys.executable, str(script), "--config-dir", str(tmp_path / "bad"), "--read-url", "http://user:pass@example.test"], capture_output=True, text=True)
    assert invalid.returncode != 0


def _free_port():
    with socket.socket() as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        return server_socket.getsockname()[1]


def test_generic_import_real_http_and_partial_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(backend_app, "DATA_DIR", tmp_path / "database")
    monkeypatch.setattr(backend_app, "ARTIFACT_DIR", tmp_path / "artifacts")
    monkeypatch.setenv("TEST_RESULTS_WRITE_TOKEN", "integration-secret")
    read_port, write_port = _free_port(), _free_port()
    servers = [
        uvicorn.Server(uvicorn.Config(backend_app.create_read_app(), host="127.0.0.1", port=read_port, log_level="error")),
        uvicorn.Server(uvicorn.Config(backend_app.create_write_app(), host="127.0.0.1", port=write_port, log_level="error")),
    ]
    threads = [threading.Thread(target=server.run, daemon=True) for server in servers]
    for thread in threads:
        thread.start()
    try:
        read_url, write_url = f"http://127.0.0.1:{read_port}", f"http://127.0.0.1:{write_port}"
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                with urlopen(read_url + "/health", timeout=0.2):
                    break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("temporary read service did not start")

        config_dir = tmp_path / "config"
        config_dir.mkdir(mode=0o700)
        config_path = config_dir / "client.json"
        config_path.write_text(json.dumps({"read_url": read_url, "write_url": write_url, "token": "integration-secret"}))
        config_path.chmod(0o600)
        image_path = tmp_path / "proof.png"
        Image.new("RGB", (2, 2), "blue").save(image_path)
        case = {
            "id": "case-1", "project_id": "generic-project", "title": "Check page", "path": ["General"],
            "requirement": "Page works", "preconditions": [], "steps": [{"action": "Open", "expected": "Page"}],
            "priority": "P1", "tags": [], "source": "bundle",
        }
        run = {
            "id": "run-1", "project_id": "generic-project", "title": "Imported", "environment": "local",
            "kind": "import", "started_at": "2026-10-27T10:00:00Z", "versions": {},
            "scope_case_ids": ["case-1"], "summary": "", "source": "bundle",
        }
        result = {
            "case_id": "case-1", "status": "passed", "actual": "Page opened", "steps": [],
            "evidence": [{"artifact_id": "source-ref", "caption": "Proof", "media_type": "image/png"}],
            "issues": [], "recorded_at": "2026-10-27T10:01:00Z", "notes": "Imported observation",
        }
        bundle_path = tmp_path / "bundle.json"
        bundle = {
            "catalog": {"project": {"id": "generic-project", "title": "Generic", "description": ""}, "cases": [case]},
            "artifacts": [{"id": "source-ref", "file": "proof.png"}],
            "runs": [{"run": run, "results": [result], "finish": {"state": "completed", "summary": "Finished"}}],
        }
        bundle_path.write_text(json.dumps(bundle))
        from scripts import import_results
        client = import_results.CLIENT_MODULE.Client(str(config_path))
        invalid_catalog = json.loads(json.dumps(bundle))
        invalid_catalog["catalog"]["cases"].append(json.loads(json.dumps(case)))
        with pytest.raises(ValueError, match="用例编号重复"):
            import_results.validate_bundle(invalid_catalog, tmp_path)
        invalid_catalog = json.loads(json.dumps(bundle))
        invalid_catalog["catalog"]["cases"][0]["project_id"] = "other-project"
        with pytest.raises(ValueError, match="用例项目"):
            import_results.validate_bundle(invalid_catalog, tmp_path)
        client.request("PUT", "/write/catalog", bundle["catalog"])
        client.request("POST", "/write/runs", run)
        uploaded = client.upload(image_path)
        prior_result = json.loads(json.dumps(result))
        prior_result["evidence"][0]["artifact_id"] = uploaded["artifact_id"]
        client.request("POST", "/write/runs/run-1/results", prior_result)

        other_case = {**case, "id": "other-case", "project_id": "other-project"}
        other_catalog = {"project": {"id": "other-project", "title": "Other", "description": ""}, "cases": [other_case]}
        other_run = {**run, "id": "global-conflict", "project_id": "other-project", "scope_case_ids": ["other-case"]}
        client.request("PUT", "/write/catalog", other_catalog)
        client.request("POST", "/write/runs", other_run)

        def read_persisted_state():
            return {
                "projects": client.request("GET", "/api/projects"),
                "cases": client.request("GET", "/api/projects/generic-project/cases"),
                "runs": client.request("GET", "/api/projects/generic-project/runs"),
                "other_run": client.request("GET", "/api/runs/global-conflict"),
                "artifact_count": len(list((tmp_path / "artifacts").iterdir())),
            }

        before_invalid_imports = read_persisted_state()
        collision_bundle = json.loads(json.dumps(bundle))
        collision_bundle["catalog"]["project"]["title"] = "Must not be written"
        collision_bundle["runs"][0]["run"]["id"] = "global-conflict"
        bundle_path.write_text(json.dumps(collision_bundle))
        with pytest.raises(ValueError, match="已被其他项目占用"):
            import_results.import_bundle(bundle_path, str(config_path))
        assert read_persisted_state() == before_invalid_imports

        invalid_files = [
            ("bad-image.png", b"not a PNG", 415),
            ("unsupported.bin", b"not a supported artifact", 415),
            ("oversized.txt", None, 413),
        ]
        for index, (filename, content, expected_status) in enumerate(invalid_files):
            artifact_path = tmp_path / filename
            if content is None:
                with artifact_path.open("wb") as artifact_file:
                    artifact_file.truncate(backend_app.MAX_UPLOAD + 1)
            else:
                artifact_path.write_bytes(content)
            invalid_bundle = json.loads(json.dumps(bundle))
            invalid_bundle["catalog"]["project"]["title"] = "Must not be written"
            invalid_bundle["catalog"]["cases"][0]["title"] = "Must not be written"
            invalid_bundle["artifacts"] = [{"id": f"invalid-ref-{index}", "file": filename}]
            invalid_bundle["runs"][0]["run"]["id"] = f"invalid-artifact-run-{index}"
            invalid_bundle["runs"][0]["results"][0]["evidence"][0]["artifact_id"] = f"invalid-ref-{index}"
            bundle_path.write_text(json.dumps(invalid_bundle))
            with pytest.raises(HTTPException) as error:
                import_results.import_bundle(bundle_path, str(config_path))
            assert error.value.status_code == expected_status
            assert read_persisted_state() == before_invalid_imports

        original = client.request("GET", "/api/runs/run-1")
        for field, changed in [("environment", "staging"), ("versions", {"service": "different-version"})]:
            incompatible = json.loads(json.dumps(bundle))
            incompatible["runs"][0]["run"][field] = changed
            bundle_path.write_text(json.dumps(incompatible))
            with pytest.raises(ValueError, match="定义与 bundle 不一致"):
                import_results.import_bundle(bundle_path, str(config_path))
            assert client.request("GET", "/api/runs/run-1") == original
        bundle_path.write_text(json.dumps(bundle))
        import_results.import_bundle(bundle_path, str(config_path))
        detail = client.request("GET", "/api/runs/run-1")
        assert detail["run"]["state"] == "completed"
        assert detail["cases"][0]["result"]["status"] == "passed"
        assert detail["cases"][0]["result"]["evidence"][0]["artifact_id"] == uploaded["artifact_id"]
        assert len(list((tmp_path / "artifacts").iterdir())) == 1
    finally:
        for server in servers:
            server.should_exit = True
        for thread in threads:
            thread.join(timeout=5)
