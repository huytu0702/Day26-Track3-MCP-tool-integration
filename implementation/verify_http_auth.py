import asyncio
import os
import subprocess
import sys
from collections.abc import Awaitable, Callable

from fastmcp import Client

TOKEN = "dev-lab-token"
URL = "http://127.0.0.1:8765/mcp"


async def wait_for_server(check: Callable[[], Awaitable[None]]) -> None:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            await check()
            return
        except Exception as error:  # noqa: BLE001
            last_error = error
            await asyncio.sleep(0.5)
    raise RuntimeError(f"HTTP auth server did not become ready: {last_error}")


async def ping_with_auth() -> None:
    async with Client(URL, auth=TOKEN) as client:
        await client.ping()


async def ping_without_auth() -> None:
    async with Client(URL) as client:
        await client.ping()


async def verify_auth() -> None:
    env = {**os.environ, "SQLITE_LAB_AUTH_TOKEN": TOKEN}
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "implementation.mcp_server",
            "--transport",
            "http",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        await wait_for_server(ping_with_auth)
        print("Authenticated HTTP ping succeeded")

        try:
            await ping_without_auth()
        except Exception:
            print("Unauthenticated HTTP ping was rejected")
            return

        raise RuntimeError("Unauthenticated HTTP ping unexpectedly succeeded")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    asyncio.run(verify_auth())
