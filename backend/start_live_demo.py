"""One-command launcher for ExitLens Backend + Public HTTPS Tunnel.

Starts an SSH reverse tunnel via `localhost.run`, sets `PUBLIC_DEMO_BASE_URL`
automatically so preset runs from the frontend use live TinyFish against `/demo-site/*`,
and runs the FastAPI server on http://localhost:8000.

Usage:
    cd backend
    ./venv/bin/python start_live_demo.py
    ./venv/bin/python start_live_demo.py --no-tunnel   # Offline/mock fallback only
"""

import argparse
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv  # noqa: E402
import uvicorn  # noqa: E402

load_dotenv(Path(__file__).parent / ".env")


def start_ssh_tunnel(port: int) -> tuple[subprocess.Popen[str] | None, str | None]:
    try:
        proc = subprocess.Popen(
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "ServerAliveInterval=15",
                "-R",
                f"80:127.0.0.1:{port}",
                "nokey@localhost.run",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Could not start ssh tunnel ({exc}); continuing in mock fallback mode.")
        return None, None

    pattern = re.compile(r"(https://[a-z0-9]+\.lhr\.life)")
    deadline = time.time() + 20
    assert proc.stdout is not None
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        m = pattern.search(line)
        if m:
            public_url = m.group(1)

            def _drain() -> None:
                assert proc.stdout is not None
                for _ in proc.stdout:
                    pass

            threading.Thread(target=_drain, daemon=True).start()
            return proc, public_url

    proc.terminate()
    print("[WARN] Tunnel timed out; continuing in mock fallback mode.")
    return None, None


def pick_bind_port(host: str, preferred_port: int) -> int:
    for candidate in [preferred_port, 8001, 8080, 8765]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
                return candidate
            except OSError:
                continue
    return preferred_port


def main() -> int:
    parser = argparse.ArgumentParser(description="Start ExitLens backend with auto HTTPS tunnel.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument(
        "--no-tunnel",
        action="store_true",
        help="Skip opening an SSH tunnel (uses mock fallback when start_url is omitted).",
    )
    args = parser.parse_args()
    bind_port = pick_bind_port(args.host, args.port)
    if bind_port != args.port:
        print(f"[INFO] Port {args.port} is already in use; binding to port {bind_port} instead.")

    tunnel_proc: subprocess.Popen[str] | None = None
    if not args.no_tunnel and not os.getenv("PUBLIC_DEMO_BASE_URL"):
        print(f"Opening public HTTPS tunnel to 127.0.0.1:{bind_port} via localhost.run...")
        tunnel_proc, public_url = start_ssh_tunnel(bind_port)
        if public_url:
            os.environ["PUBLIC_DEMO_BASE_URL"] = public_url

    public_base = os.getenv("PUBLIC_DEMO_BASE_URL")
    print("=" * 64)
    print(f"ExitLens Backend Ready:   http://localhost:{bind_port}")
    print(f"Swagger API Docs:         http://localhost:{bind_port}/docs")
    print(f"Curated Presets Endpoint: http://localhost:{bind_port}/presets")
    if public_base:
        print(f"Public Tunnel Active:     {public_base}")
        print(f"  - StreamFlix India:     {public_base}/demo-site/")
        print(f"  - GanaPlus Music:       {public_base}/demo-site/music.html")
        print(f"  - QuickCart Pro (Fair): {public_base}/demo-site/fair.html")
        print(f"  - CineVeil VIP (Block): {public_base}/demo-site/blocked.html")
    else:
        print("Public Tunnel:            Disabled (using deterministic mock fallback for local runs)")
    print("=" * 64, flush=True)

    try:
        from main import app

        uvicorn.run(app, host=args.host, port=bind_port)
    finally:
        if tunnel_proc is not None:
            tunnel_proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
