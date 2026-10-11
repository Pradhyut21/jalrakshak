"""Check incident-specific approval in Chromium using an isolated simulated session."""
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import urllib.request

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def run():
    checks, errors = [], []
    failure = None
    with TemporaryDirectory(prefix="jalrakshak-incident-progress-") as temporary:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env.update(JAL_STORAGE="sqlite", JAL_DB_PATH=str(Path(temporary) / "test.sqlite3"),
                   ALLOWED_ORIGINS=url, JAL_COOKIE_SECURE="false")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", str(ROOT / "backend"),
             "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
            cwd=ROOT, env=env, creationflags=flags,
        )
        try:
            for attempt in range(60):
                if server.poll() is not None:
                    raise RuntimeError("Isolated server stopped before the check")
                try:
                    with urllib.request.urlopen(url, timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.25)
            else:
                raise RuntimeError("Isolated server did not start")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    context = browser.new_context(viewport={"width": 1440, "height": 1000})
                    page = context.new_page()
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    response = context.request.get(url + "/api/dashboard")
                    assert response.ok
                    initial = response.json()
                    assert initial["mode"] == "SIMULATED_DEMO"
                    csrf = initial["csrf_token"]

                    def post(path, data):
                        response = context.request.post(url + "/api" + path, data=data,
                                                        headers={"X-CSRF-Token": csrf})
                        assert response.ok, f"{path}: HTTP {response.status}"
                        return response.json()

                    def approval_step(complete):
                        page.goto(url)
                        step = page.locator(".incident-progress .progress-step").filter(
                            has=page.get_by_text("Request approved", exact=True))
                        expect(step).to_have_count(1)
                        complete_class = re.compile(r"\bcomplete\b")
                        if complete:
                            expect(step).to_have_class(complete_class)
                        else:
                            expect(step).not_to_have_class(complete_class)

                    assert initial["incident"] is None
                    approval_step(False)
                    checks.append("No incident has no completed approval step")

                    old = post("/actions/propose", {"type": "REQUEST_SUPPLY"})
                    assert old["incident_id"] is None
                    before_incident = post(f"/actions/{old['id']}/approve",
                                           {"evidence_version": old["evidence_version"], "confirmed": True})
                    assert before_incident["incident"] is None
                    assert before_incident["actions"][-1]["status"] == "LOCAL_RECEIVED"
                    approval_step(False)
                    checks.append("An approved pre-incident notice does not complete approval without an incident")

                    opened = post("/demo/scenario", {"scenario": "excess_usage", "hours": 3})
                    incident = opened["incident"]
                    assert incident and incident["status"] == "OPEN" and not incident.get("approved_action_id")
                    assert opened["actions"][-1]["incident_id"] is None
                    approval_step(False)
                    checks.append("A new OPEN incident remains visually unapproved despite a historical local receipt")

                    current = post("/actions/propose", {"type": "REQUEST_SUPPLY"})
                    assert current["incident_id"] == incident["id"]
                    approval_step(False)
                    checks.append("An unapproved proposal for the current incident does not complete approval")

                    approved = post(f"/actions/{current['id']}/approve",
                                    {"evidence_version": current["evidence_version"], "confirmed": True})
                    assert approved["incident"]["approved_action_id"] == current["id"]
                    assert approved["actions"][-1]["published_at"] is None
                    approval_step(True)
                    checks.append("Approval of the current incident completes its step with a local receipt only")
                    assert not errors, errors
                finally:
                    browser.close()
        except Exception as exc:
            failure = f"{type(exc).__name__}: {exc}"
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
    report = {
        "status": "FAIL" if failure else "PASS", "checked_at_utc": datetime.now(UTC).isoformat(),
        "tool": "Playwright / Chromium", "checks": checks, "unexpected_page_errors": errors,
        "failure": failure, "test_inputs": "Isolated generated SIMULATED_DEMO session, not field data",
        "limits": "Focused browser/HTTP regression; no full browser suite, AWS or external notification check",
    }
    (ROOT / "artifacts/incident-progress-verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
