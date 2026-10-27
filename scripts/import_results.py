#!/usr/bin/env python3
"""通过录入接口导入与业务项目无关的 JSON 结果包。"""
import argparse
import copy
import importlib.util
import json
import mimetypes
from pathlib import Path
import tempfile
import urllib.error

from backend.app import MAX_UPLOAD, Catalog, Finish, Result, Run, identifier, validate_artifact

ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "skills/test-results/scripts/client.py"
CLIENT_SPEC = importlib.util.spec_from_file_location("test_results_client", CLIENT_PATH)
CLIENT_MODULE = importlib.util.module_from_spec(CLIENT_SPEC)
CLIENT_SPEC.loader.exec_module(CLIENT_MODULE)


def validate_bundle(bundle: object, bundle_dir: Path) -> tuple[dict, dict[str, Path], list[dict]]:
    if not isinstance(bundle, dict) or set(bundle) != {"catalog", "artifacts", "runs"}:
        raise ValueError("bundle 必须仅包含 catalog、artifacts、runs")
    catalog = Catalog.model_validate(bundle["catalog"]).model_dump(mode="json")
    case_ids = [case["id"] for case in catalog["cases"]]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("catalog 用例编号重复")
    if any(case["project_id"] != catalog["project"]["id"] for case in catalog["cases"]):
        raise ValueError("catalog 用例项目与项目编号不一致")
    cases = {case["id"]: case for case in catalog["cases"]}
    artifacts = {}
    for item in bundle["artifacts"]:
        if not isinstance(item, dict) or set(item) != {"id", "file"} or not isinstance(item["id"], str) or not item["id"]:
            raise ValueError("artifact 必须包含非空 id 和相对 file 路径")
        if item["id"] in artifacts:
            raise ValueError(f"重复的 artifact 引用：{item['id']}")
        relative = Path(item["file"])
        if relative.is_absolute():
            raise ValueError("artifact 文件路径必须相对 bundle 文件所在目录")
        file = (bundle_dir / relative).resolve(strict=True)
        if not file.is_file() or not file.is_relative_to(bundle_dir.resolve()):
            raise ValueError(f"artifact 文件必须是 bundle 目录内的普通文件：{item['file']}")
        artifacts[item["id"]] = file

    runs = []
    run_ids = set()
    for entry in bundle["runs"]:
        if not isinstance(entry, dict) or set(entry) != {"run", "results", "finish"}:
            raise ValueError("每个轮次必须包含 run、results、finish")
        run = Run.model_validate(entry["run"]).model_dump(mode="json")
        finish = Finish.model_validate(entry["finish"]).model_dump(mode="json")
        if run["id"] in run_ids:
            raise ValueError(f"轮次编号重复：{run['id']}")
        run_ids.add(run["id"])
        if run["project_id"] != catalog["project"]["id"]:
            raise ValueError("轮次项目必须与 bundle catalog 项目一致")
        if len(set(run["scope_case_ids"])) != len(run["scope_case_ids"]) or any(case_id not in cases for case_id in run["scope_case_ids"]):
            raise ValueError(f"轮次 {run['id']} 范围包含重复或未知用例")
        results = [Result.model_validate(result).model_dump(mode="json") for result in entry["results"]]
        result_ids = set()
        for result in results:
            if result["case_id"] not in run["scope_case_ids"] or result["case_id"] in result_ids:
                raise ValueError(f"轮次 {run['id']} 的结果超出范围或用例重复")
            result_ids.add(result["case_id"])
            for evidence in [*result["evidence"], *(ev for step in result["steps"] for ev in step["evidence"])]:
                artifact_id = evidence["artifact_id"]
                if artifact_id not in artifacts:
                    identifier(artifact_id)
        runs.append({"run": run, "results": results, "finish": finish})
    return catalog, artifacts, runs


def evidence_items(result: dict) -> list[dict]:
    return [*result["evidence"], *(evidence for step in result["steps"] for evidence in step["evidence"])]


def same_result(existing: dict, incoming: dict, source_files: dict[str, Path], client, artifact_ids: dict[str, str]) -> bool:
    """续传时核对实际附件内容，不能将输入文件中的引用编号当成受管附件编号。"""
    left = copy.deepcopy(existing)
    right = copy.deepcopy(incoming)
    existing_evidence = evidence_items(left)
    incoming_evidence = evidence_items(right)
    if len(existing_evidence) != len(incoming_evidence):
        return False
    for old, new in zip(existing_evidence, incoming_evidence):
        source = source_files.get(new["artifact_id"])
        if source is None:
            if old != new:
                return False
            continue
        old_without_id = {key: value for key, value in old.items() if key != "artifact_id"}
        new_without_id = {key: value for key, value in new.items() if key != "artifact_id"}
        if old_without_id != new_without_id:
            return False
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "artifact"
            client.download(old["artifact_id"], target)
            if target.read_bytes() != source.read_bytes():
                return False
        previous_id = artifact_ids.get(new["artifact_id"])
        if previous_id is not None and previous_id != old["artifact_id"]:
            raise ValueError(f"source-ref {new['artifact_id']} 对应多个不同受管附件")
        artifact_ids[new["artifact_id"]] = old["artifact_id"]
        old["artifact_id"] = new["artifact_id"]
    return left == right


def import_bundle(bundle_path: Path, config: str | None = None) -> None:
    """在写入前排除编号、附件和结果冲突；中断后保留已保存结果，继续尚未完成的录入。"""
    bundle_path = bundle_path.resolve(strict=True)
    raw_bundle = json.loads(bundle_path.read_text())
    catalog, artifact_files, runs = validate_bundle(raw_bundle, bundle_path.parent)
    client = CLIENT_MODULE.Client(config)

    existing_runs = {run["id"]: run for run in client.request("GET", f"/api/projects/{catalog['project']['id']}/runs")}
    run_details = {}
    active = []
    for entry in runs:
        run = entry["run"]
        current = existing_runs.get(run["id"])
        if current is None:
            try:
                client.request("GET", f"/api/runs/{run['id']}")
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
            else:
                raise ValueError(f"轮次编号 {run['id']} 已被其他项目占用")
        if current and current["state"] != "running":
            continue
        if current:
            detail = client.request("GET", f"/api/runs/{run['id']}")
            actual_run = detail["run"]
            if {key: actual_run[key] for key in run} != run:
                raise ValueError(f"运行中的轮次 {run['id']} 定义与 bundle 不一致")
            expected_cases = {case_id: next(case for case in catalog["cases"] if case["id"] == case_id) for case_id in run["scope_case_ids"]}
            actual_cases = {item["case"]["id"]: item["case"] for item in detail["cases"]}
            if actual_cases != expected_cases:
                raise ValueError(f"运行中的轮次 {run['id']} 用例定义与 bundle 不一致")
            run_details[run["id"]] = {item["case"]["id"]: item["result"] for item in detail["cases"]}
        active.append(entry)

    if not active:
        print("bundle 中的轮次均已结束，保留现有记录。")
        return
    source_artifact_ids = {
        evidence["artifact_id"]
        for entry in active
        for result in entry["results"]
        for evidence in evidence_items(result)
        if evidence["artifact_id"] in artifact_files
    }
    for artifact_id in sorted(source_artifact_ids):
        path = artifact_files[artifact_id]
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as file:
            validate_artifact(file.read(MAX_UPLOAD + 1), media_type)

    managed_artifacts = {
        evidence["artifact_id"]
        for entry in active
        for result in entry["results"]
        for evidence in evidence_items(result)
        if evidence["artifact_id"] not in artifact_files
    }
    with tempfile.TemporaryDirectory() as directory:
        for index, artifact_id in enumerate(sorted(managed_artifacts)):
            client.download(artifact_id, Path(directory) / str(index))

    artifact_ids = {}
    prepared = []
    for entry in active:
        run = entry["run"]
        saved = run_details.get(run["id"], {})
        pending = []
        for result in entry["results"]:
            old = saved.get(result["case_id"])
            if old is None:
                pending.append(result)
            elif not same_result(old, result, artifact_files, client, artifact_ids):
                raise ValueError(f"轮次 {run['id']} 用例 {result['case_id']} 已有不同结果，拒绝覆盖")
        prepared.append((entry, pending))

    client.request("PUT", "/write/catalog", catalog)

    for entry, pending in prepared:
        run = entry["run"]
        for result in pending:
            for evidence in evidence_items(result):
                source_id = evidence["artifact_id"]
                if source_id in artifact_files and source_id not in artifact_ids:
                    uploaded = client.upload(artifact_files[source_id])
                    artifact_ids[source_id] = uploaded["artifact_id"]

        if run["id"] not in existing_runs:
            client.request("POST", "/write/runs", run)
        for result in pending:
            payload = copy.deepcopy(result)
            for evidence in evidence_items(payload):
                evidence["artifact_id"] = artifact_ids.get(evidence["artifact_id"], evidence["artifact_id"])
            client.request("POST", f"/write/runs/{run['id']}/results", payload)
        client.request("POST", f"/write/runs/{run['id']}/finish", entry["finish"])
        print(f"已导入轮次 {run['id']}，新增 {len(pending)} 项结果。")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="bundle.json 文件")
    parser.add_argument("--config", help="私有客户端配置，默认 ~/.config/test-results/client.json")
    args = parser.parse_args()
    import_bundle(args.file, args.config)


if __name__ == "__main__":
    main()
