"""Standalone TinyFish Web Agent smoke test.

Runs one goal against a URL and prints every streamed event.
Uses the official `tinyfish` SDK (verified against v0.11.0), which calls
POST https://agent.tinyfish.ai/v1/automation/run-sse with the X-API-Key header.

Usage:
    python tinyfish_test.py https://example.com
    python tinyfish_test.py https://example.com --goal "Find the pricing page and list the plans."

Reads TINYFISH_API_KEY from the environment (or backend/.env).
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from tinyfish import (
    CompleteEvent,
    HeartbeatEvent,
    ProgressEvent,
    StartedEvent,
    StreamingUrlEvent,
    TinyFish,
)

DEFAULT_GOAL = (
    "Find where a user would cancel their subscription on this site. "
    "Describe each step you take. STOP before clicking any final cancel or confirm "
    "button - do not click it. Return JSON with keys: steps (list of strings), "
    "stopped_at_button (string or null), cancellation_completed (boolean)."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one TinyFish agent goal and print every event.")
    parser.add_argument("url", help="Starting URL for the agent")
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="Natural-language goal for the agent")
    args = parser.parse_args()

    load_dotenv()
    if not os.getenv("TINYFISH_API_KEY"):
        print("TINYFISH_API_KEY is not set (export it or put it in backend/.env).", file=sys.stderr)
        return 1

    client = TinyFish()  # reads TINYFISH_API_KEY from the environment

    with client.agent.stream(url=args.url, goal=args.goal) as stream:
        for event in stream:
            if isinstance(event, StartedEvent):
                print(f"[STARTED] run_id={event.run_id}")
            elif isinstance(event, StreamingUrlEvent):
                print(f"[STREAMING_URL] {event.streaming_url}")
            elif isinstance(event, ProgressEvent):
                print(f"[PROGRESS] {event.purpose}")
            elif isinstance(event, HeartbeatEvent):
                print("[HEARTBEAT]")
            elif isinstance(event, CompleteEvent):
                print(f"[COMPLETE] status={event.status}")
                if event.error:
                    print(f"  error: {event.error}")
                print(f"  result_json: {event.result_json}")
            else:
                print(f"[OTHER] {event!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
