#!/usr/bin/env python3
"""Navigate Safari to a URL through the WebDriver HTTP protocol."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class WebDriverStep:
    name: str
    ok: bool
    status: int | None
    response: dict[str, Any] | None
    error: str


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 10) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="ignore")
        return response.status, json.loads(body) if body else {}


def step(name: str, method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 10) -> WebDriverStep:
    try:
        status, response = request_json(method, url, payload, timeout)
        return WebDriverStep(name, 200 <= status < 300, status, response, "")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        try:
            response = json.loads(body) if body else {}
        except json.JSONDecodeError:
            response = {"raw": body}
        return WebDriverStep(name, False, exc.code, response, str(exc))
    except Exception as exc:  # noqa: BLE001 - navigation result should preserve the exact local failure.
        return WebDriverStep(name, False, None, None, str(exc))


def session_id_from(response: dict[str, Any] | None) -> str:
    if not response:
        return ""
    value = response.get("value")
    if isinstance(value, dict):
        if isinstance(value.get("sessionId"), str):
            return value["sessionId"]
    if isinstance(response.get("sessionId"), str):
        return str(response["sessionId"])
    return ""


def value_from(response: dict[str, Any] | None) -> Any:
    if not response:
        return None
    return response.get("value")


def wait_for_driver(base_url: str, timeout: int) -> WebDriverStep:
    deadline = time.monotonic() + timeout
    last = WebDriverStep("status", False, None, None, "not attempted")
    while time.monotonic() < deadline:
        last = step("status", "GET", f"{base_url}/status", timeout=2)
        if last.ok:
            return last
        time.sleep(0.25)
    return last


def run_navigation(args: argparse.Namespace) -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{args.port}"
    log_path = Path(args.safaridriver_log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    process: subprocess.Popen[bytes] | None = None
    with log_path.open("ab") as log:
        if not args.reuse_running_driver:
            process = subprocess.Popen(
                ["safaridriver", "-p", str(args.port)],
                stdout=log,
                stderr=log,
            )
        started_at = now_utc()
        steps: list[WebDriverStep] = []
        status = wait_for_driver(base_url, args.driver_start_timeout)
        steps.append(status)
        session_id = ""
        current_url = ""
        title = ""
        if status.ok:
            create = step(
                "create_session",
                "POST",
                f"{base_url}/session",
                {
                    "capabilities": {
                        "alwaysMatch": {
                            "browserName": "safari",
                        }
                    }
                },
                timeout=args.command_timeout,
            )
            steps.append(create)
            session_id = session_id_from(create.response)
            if session_id:
                steps.append(
                    step(
                        "set_timeouts",
                        "POST",
                        f"{base_url}/session/{session_id}/timeouts",
                        {
                            "pageLoad": args.page_load_timeout_ms,
                            "script": args.script_timeout_ms,
                            "implicit": 0,
                        },
                        timeout=args.command_timeout,
                    )
                )
                steps.append(
                    step(
                        "navigate",
                        "POST",
                        f"{base_url}/session/{session_id}/url",
                        {"url": args.url},
                        timeout=args.command_timeout,
                    )
                )
                time.sleep(args.wait_seconds)
                get_url = step("current_url", "GET", f"{base_url}/session/{session_id}/url", timeout=args.command_timeout)
                steps.append(get_url)
                value = value_from(get_url.response)
                current_url = value if isinstance(value, str) else ""
                get_title = step("title", "GET", f"{base_url}/session/{session_id}/title", timeout=args.command_timeout)
                steps.append(get_title)
                title_value = value_from(get_title.response)
                title = title_value if isinstance(title_value, str) else ""
                steps.append(step("delete_session", "DELETE", f"{base_url}/session/{session_id}", timeout=args.command_timeout))
        completed_at = now_utc()
    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    navigation_ok = bool(session_id) and any(item.name == "navigate" and item.ok for item in steps)
    return {
        "started_at": started_at,
        "completed_at": completed_at,
        "url": args.url,
        "base_url": base_url,
        "reuse_running_driver": args.reuse_running_driver,
        "session_id_present": bool(session_id),
        "navigation_ok": navigation_ok,
        "wait_seconds": args.wait_seconds,
        "current_url": current_url,
        "title": title,
        "steps": [asdict(item) for item in steps],
        "safaridriver_log": args.safaridriver_log,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--port", type=int, default=4444)
    parser.add_argument("--wait-seconds", type=float, default=8)
    parser.add_argument("--driver-start-timeout", type=int, default=10)
    parser.add_argument("--command-timeout", type=int, default=30)
    parser.add_argument("--page-load-timeout-ms", type=int, default=30000)
    parser.add_argument("--script-timeout-ms", type=int, default=30000)
    parser.add_argument("--safaridriver-log", default="/tmp/safaridriver.log")
    parser.add_argument("--reuse-running-driver", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    result = run_navigation(args)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["navigation_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
