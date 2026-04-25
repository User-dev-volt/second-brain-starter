"""
comfyui_integration.py — ComfyUI local API client for Alec's asset generation.

Auth: None (local HTTP, http://localhost:8188)
No install needed beyond `requests` and `websocket-client`.

Operations:
  get_queue_status()              — Current queue state
  submit_workflow(workflow)       — Submit a workflow JSON, return prompt_id
  poll_result(prompt_id, timeout) — Poll until job completes
  get_recent_outputs(limit)       — Recent generation history from /history
  save_image(filename, dest_path) — Download a generated image to disk

Install: pip install requests websocket-client
"""

import json
import time
import sys
from pathlib import Path

COMFY_BASE = "http://localhost:8188"


def _get(path: str, params: dict = None) -> dict:
    try:
        import requests
    except ImportError:
        print("requests not installed. Run: pip install requests", file=sys.stderr)
        sys.exit(1)
    resp = requests.get(f"{COMFY_BASE}{path}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, data: dict) -> dict:
    try:
        import requests
    except ImportError:
        print("requests not installed. Run: pip install requests", file=sys.stderr)
        sys.exit(1)
    resp = requests.post(f"{COMFY_BASE}{path}", json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_queue_status() -> dict:
    """Return the current ComfyUI queue status."""
    return _get("/queue")


def submit_workflow(workflow: dict) -> str:
    """Submit a workflow JSON dict. Returns the prompt_id."""
    result = _post("/prompt", {"prompt": workflow})
    return result["prompt_id"]


def poll_result(prompt_id: str, timeout: int = 300) -> dict:
    """Poll /history until the job completes or timeout is reached."""
    start = time.time()
    while time.time() - start < timeout:
        history = _get(f"/history/{prompt_id}")
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"ComfyUI job {prompt_id} did not complete within {timeout}s")


def get_recent_outputs(limit: int = 20) -> list:
    """Return the most recent N generation results from history."""
    history = _get("/history")
    items = list(history.values())
    return items[-limit:]


def save_image(filename: str, dest_path: str):
    """Download a generated image from ComfyUI output to dest_path."""
    try:
        import requests
    except ImportError:
        print("requests not installed. Run: pip install requests", file=sys.stderr)
        sys.exit(1)
    resp = requests.get(
        f"{COMFY_BASE}/view",
        params={"filename": filename},
        timeout=30,
    )
    resp.raise_for_status()
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)


def watch_via_websocket(on_complete=None):
    """
    Connect to ComfyUI WebSocket and call on_complete(prompt_id, output)
    when a generation finishes. Blocks until interrupted.
    """
    try:
        import websocket
    except ImportError:
        print("websocket-client not installed. Run: pip install websocket-client", file=sys.stderr)
        sys.exit(1)

    ws_url = f"ws://localhost:8188/ws"
    ws = websocket.WebSocket()
    ws.connect(ws_url)
    print(f"Watching ComfyUI at {ws_url} ...")

    try:
        while True:
            raw = ws.recv()
            if isinstance(raw, str):
                msg = json.loads(raw)
                if msg.get("type") == "executed":
                    data = msg.get("data", {})
                    prompt_id = data.get("prompt_id")
                    output = data.get("output", {})
                    if on_complete:
                        on_complete(prompt_id, output)
                    else:
                        print(f"Completed: {prompt_id}")
                        print(json.dumps(output, indent=2))
    except KeyboardInterrupt:
        pass
    finally:
        ws.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ComfyUI integration")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("queue", help="Show current queue status")

    p_recent = sub.add_parser("recent", help="Recent generation history")
    p_recent.add_argument("--limit", type=int, default=10)

    p_submit = sub.add_parser("submit", help="Submit a workflow JSON file")
    p_submit.add_argument("workflow_file")

    p_watch = sub.add_parser("watch", help="Watch for completions via WebSocket")

    args = parser.parse_args()

    if args.cmd == "queue":
        print(json.dumps(get_queue_status(), indent=2))

    elif args.cmd == "recent":
        items = get_recent_outputs(args.limit)
        print(f"{len(items)} recent outputs:")
        for item in items:
            outputs = item.get("outputs", {})
            for node_id, node_out in outputs.items():
                images = node_out.get("images", [])
                for img in images:
                    print(f"  {img.get('filename')} ({img.get('type')})")

    elif args.cmd == "submit":
        workflow_path = Path(args.workflow_file)
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        prompt_id = submit_workflow(workflow)
        print(f"Submitted: {prompt_id}")
        print("Polling for result...")
        result = poll_result(prompt_id)
        print(json.dumps(result, indent=2))

    elif args.cmd == "watch":
        watch_via_websocket()

    else:
        parser.print_help()
