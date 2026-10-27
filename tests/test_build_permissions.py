"""共享缓存只由可信主线构建写入，PR 使用相同检查但不获得写权限。"""

from pathlib import Path

import yaml


def test_pr_image_check_has_no_registry_write_permission():
    root = Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())
    main = ci["jobs"]["image-smoke"]
    pr = ci["jobs"]["image-smoke-pr"]
    assert main["if"] == "github.event_name == 'push' && github.ref == 'refs/heads/main'"
    assert main["permissions"]["packages"] == "write"
    assert main["with"]["export-cache"] is True
    assert pr["if"] == "github.event_name == 'pull_request'"
    assert "write" not in pr["permissions"].values()
    assert not pr.get("with", {}).get("export-cache", False)
    assert main["uses"] == pr["uses"] == "./.github/workflows/image-check.yml"

    shared = yaml.safe_load((root / ".github/workflows/image-check.yml").read_text())
    assert "permissions" not in shared
    assert "permissions" not in shared["jobs"]["check"]
