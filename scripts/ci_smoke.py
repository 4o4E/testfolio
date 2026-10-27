"""Start a built Testfolio image and verify its unauthenticated HTTP contract."""

import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(url, *, method="GET", data=None):
    req = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    return urlopen(req, timeout=3)


def main(image):
    with tempfile.TemporaryDirectory(prefix="testfolio-ci-") as temporary:
        root = os.path.join(temporary, "state")
        os.makedirs(root)
        token = secrets.token_urlsafe(32)
        container = subprocess.run(
            [
                "docker", "run", "--detach", "--rm",
                "--user", f"{os.getuid()}:{os.getgid()}",
                "--publish", "127.0.0.1::8080",
                "--publish", "127.0.0.1::8081",
                "--volume", f"{root}:/state",
                "--env", "TEST_RESULTS_DATA_DIR=/state/sqlite",
                "--env", "TEST_RESULTS_ARTIFACT_DIR=/state/artifacts",
                "--env", "TEST_RESULTS_WRITE_TOKEN",
                image,
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "TEST_RESULTS_WRITE_TOKEN": token},
        ).stdout.strip()
        try:
            ports = {}
            for container_port in (8080, 8081):
                mapping = subprocess.run(
                    ["docker", "port", container, f"{container_port}/tcp"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                ports[container_port] = mapping.rsplit(":", 1)[1]
            read_base = f"http://127.0.0.1:{ports[8080]}"
            write_base = f"http://127.0.0.1:{ports[8081]}"

            for base in (read_base, write_base):
                deadline = time.monotonic() + 60
                while True:
                    try:
                        with request(base + "/health") as response:
                            if json.load(response) != {"status": "ok"}:
                                raise RuntimeError("Health endpoint returned an unexpected response")
                        break
                    # Docker can accept TCP before the application's HTTP listener is ready.
                    except (URLError, TimeoutError, ConnectionError):
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(1)

            with request(read_base + "/") as response:
                page = response.read().decode()
                if response.status != 200 or "<html" not in page.lower():
                    raise RuntimeError("Root page did not serve the application")
            with request(read_base + "/api/projects") as response:
                if json.load(response) != []:
                    raise RuntimeError("Fresh image unexpectedly contains project records")
            try:
                request(read_base + "/write/catalog", method="PUT", data=b"{}")
            except HTTPError as error:
                if error.code != 404:
                    raise RuntimeError(f"Write route on read service returned HTTP {error.code}") from error
            else:
                raise RuntimeError("Read service exposed the write route")
            try:
                request(write_base + "/write/catalog", method="PUT", data=b"{}")
            except HTTPError as error:
                if error.code != 401:
                    raise RuntimeError(f"Unauthenticated write returned HTTP {error.code}") from error
            else:
                raise RuntimeError("Unauthenticated write was accepted")
            print("Container HTTP smoke check passed")
        except Exception:
            subprocess.run(["docker", "logs", container], check=True)
            raise
        finally:
            subprocess.run(["docker", "stop", container], check=True, capture_output=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/ci_smoke.py IMAGE")
    main(sys.argv[1])
