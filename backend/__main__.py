import asyncio
import os

import uvicorn

from .app import create_read_app, create_write_app


async def main() -> None:
    if not os.environ.get("TEST_RESULTS_WRITE_TOKEN"):
        raise RuntimeError("TEST_RESULTS_WRITE_TOKEN must be configured")
    read_server = uvicorn.Server(uvicorn.Config(create_read_app(), host="0.0.0.0", port=8080))
    write_server = uvicorn.Server(uvicorn.Config(create_write_app(), host="0.0.0.0", port=8081))
    tasks = [asyncio.create_task(server.serve()) for server in (read_server, write_server)]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    for task in done:
        exception = task.exception()
        if exception:
            raise exception
    raise RuntimeError("A service server stopped unexpectedly")


if __name__ == "__main__":
    asyncio.run(main())
