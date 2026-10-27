#!/usr/bin/env python3
"""准备私有录入配置；重复运行保留现有令牌和未指定的网址。"""
import argparse
import json
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit


def checked_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username is not None or parsed.password is not None:
        raise ValueError("网址必须是有效的 HTTP(S) 地址，且不能包含账号或密码")
    if "?" in value or "#" in value:
        raise ValueError("网址不能包含查询参数或片段")
    return value.rstrip("/")


def regular_private_file(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"配置路径必须是普通文件：{path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / ".config/test-results", help="私有配置目录，默认 ~/.config/test-results")
    parser.add_argument("--read-url", help="查看服务 HTTP(S) 地址；新配置默认为 http://localhost:8080")
    parser.add_argument("--write-url", help="本机录入服务 HTTP(S) 地址；新配置默认为 http://localhost:8081")
    args = parser.parse_args()

    config_dir = args.config_dir.expanduser()
    if config_dir.is_symlink():
        raise ValueError("配置目录不能是符号链接")
    config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not config_dir.is_dir():
        raise ValueError("配置路径必须是目录")
    config_dir.chmod(0o700)
    config_file = config_dir / "client.json"
    server_file = config_dir / "server.env"
    regular_private_file(config_file)
    regular_private_file(server_file)

    if config_file.exists():
        config = json.loads(config_file.read_text())
        if not isinstance(config, dict) or not isinstance(config.get("token"), str) or not config["token"]:
            raise ValueError("现有客户端配置缺少有效令牌")
    else:
        config = {"read_url": "http://localhost:8080", "write_url": "http://localhost:8081", "token": secrets.token_urlsafe(48)}
    config["read_url"] = checked_url(args.read_url) if args.read_url is not None else checked_url(config.get("read_url", "http://localhost:8080"))
    config["write_url"] = checked_url(args.write_url) if args.write_url is not None else checked_url(config.get("write_url", "http://localhost:8081"))

    fd = os.open(config_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w") as file:
        json.dump(config, file)
    config_file.chmod(0o600)
    fd = os.open(server_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w") as file:
        file.write("TEST_RESULTS_WRITE_TOKEN=" + config["token"] + "\n")
    server_file.chmod(0o600)
    print("本机私有录入配置已准备，未输出令牌。")


if __name__ == "__main__":
    main()
