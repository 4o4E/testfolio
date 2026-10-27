import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_link_cli_uses_private_config_and_quotes_path_values(tmp_path):
    config_dir = tmp_path / "private"
    config_dir.mkdir(mode=0o700)
    config_path = config_dir / "client.json"
    config_path.write_text(json.dumps({
        "read_url": "http://localhost:8080/prefix",
        "write_url": "http://localhost:8081",
        "token": "private-token-value",
    }))
    config_path.chmod(0o600)
    environment = {**os.environ, "TEST_RESULTS_CONFIG": str(config_path)}
    result = subprocess.run(
        [sys.executable, str(ROOT / "skills/test-results/scripts/client.py"), "link", "--project", "proj /?", "--run", "run?1", "--case", "case:1"],
        capture_output=True,
        text=True,
        env=environment,
        check=True,
    )
    assert result.stdout.strip() == "http://localhost:8080/prefix/projects/proj%20%2F%3F/runs/run%3F1/cases/case%3A1"
    assert "private-token-value" not in result.stdout + result.stderr


def test_link_cli_uses_explicit_config_before_environment_config(tmp_path):
    first = tmp_path / "env.json"
    second = tmp_path / "explicit.json"
    for path, host in [(first, "env.example"), (second, "explicit.example")]:
        path.write_text(json.dumps({"read_url": f"https://{host}", "write_url": "http://localhost", "token": "private"}))
        path.chmod(0o600)
    environment = {**os.environ, "TEST_RESULTS_CONFIG": str(first)}
    result = subprocess.run(
        [sys.executable, str(ROOT / "skills/test-results/scripts/client.py"), "--config", str(second), "link", "--project", "p", "--run", "r"],
        capture_output=True,
        text=True,
        env=environment,
        check=True,
    )
    assert result.stdout.strip() == "https://explicit.example/projects/p/runs/r"


def test_link_cli_rejects_invalid_urls_without_printing_config_values(tmp_path):
    invalid_urls = [
        "ftp://host.example/private-scheme",
        "https://user:private-password@host.example/path",
        "https://host.example/path?credential=private-query",
        "https://host.example/path?",
        "https://host.example/path#private-fragment",
        "https://host.example/path#",
    ]
    for index, read_url in enumerate(invalid_urls):
        config_path = tmp_path / f"invalid-{index}.json"
        config_path.write_text(json.dumps({"read_url": read_url, "write_url": "http://localhost", "token": "private-token"}))
        config_path.chmod(0o600)
        result = subprocess.run(
            [sys.executable, str(ROOT / "skills/test-results/scripts/client.py"), "--config", str(config_path), "link", "--project", "p", "--run", "r"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        for secret in [read_url.split("://", 1)[-1].split("@", 1)[0], "private-password", "private-query", "private-fragment", "private-token"]:
            assert secret not in output


def test_setup_local_rejects_query_and_fragment_without_printing_values(tmp_path):
    script = ROOT / "scripts/setup_local.py"
    invalid_urls = [
        "http://localhost:8080/?credential=private-query",
        "http://localhost:8080/?",
        "http://localhost:8080/#private-fragment",
        "http://localhost:8080/#",
    ]
    for index, read_url in enumerate(invalid_urls):
        result = subprocess.run(
            [sys.executable, str(script), "--config-dir", str(tmp_path / f"config-{index}"), "--read-url", read_url],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "private-query" not in output
        assert "private-fragment" not in output
