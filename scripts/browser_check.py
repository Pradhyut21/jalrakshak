"""Exercise the built UI against a running local API using real Chromium."""
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/screenshots"


def run(url="http://127.0.0.1:8000"):
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    errors = []
    snapshots = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        expect(page.locator(".tank-copy h2")).to_contain_text("32,000", timeout=20000)
        expect(page.get_by_text("Reserve outlook stable", exact=True)).to_be_visible()
        page.screenshot(path=str(OUT / "desktop.png"), full_page=True)
        snapshots.append("healthy 32,000 L / SAFE")
        checks.append("initial API-backed healthy state")

        page.get_by_role("button", name="What if?").click()
        page.locator("#delay").fill("24")
        page.get_by_role("button", name="Compare this plan").click()
        expect(page.locator(".preview-result")).to_be_visible()
        expect(page.locator(".preview-metrics")).to_contain_text("8.7 hours")
        page.screenshot(path=str(OUT / "scenario-preview.png"), full_page=True)
        page.get_by_role("button", name="Close dialog").click()
        expect(page.locator(".tank-copy h2")).to_contain_text("32,000")
        checks.append("24h delayed supply preview creates 8.7h projected physical shortage without mutation")

        page.get_by_role("button", name="Why is this the action deadline?").click()
        expect(page.locator(".assistant-answer")).to_contain_text("conservative reserve forecast")
        checks.append("deterministic assistant explains computed deadline")
        page.get_by_role("button", name="Excess usage", exact=True).click()
        expect(page.get_by_text("Action needed now", exact=True)).to_be_visible()
        expect(page.locator(".tank-copy h2")).to_contain_text("27,200")
        page.screenshot(path=str(OUT / "excess-usage.png"), full_page=True)
        checks.append("excess scenario updates readings, volume, risk and incident")

        page.get_by_role("button", name="Review supply request").click()
        approve = page.get_by_role("button", name="Approve demo request")
        expect(approve).to_be_disabled()
        page.get_by_role("checkbox").check()
        expect(approve).to_be_enabled()
        page.screenshot(path=str(OUT / "approval.png"), full_page=True)
        approve.click()
        expect(page.locator(".receipt-strip")).to_contain_text("Local received")
        checks.append("explicit exact-request confirmation produces truthful local receipt")
        page.get_by_role("button", name="Repair + readings").click()
        expect(page.locator(".incident-card")).to_contain_text("Verifying")
        page.get_by_role("button", name="Demo refill", exact=True).click()
        expect(page.locator(".incident-card")).to_contain_text("Resolved", timeout=20000)
        expect(page.get_by_text("Reserve outlook stable", exact=True)).to_be_visible()
        page.screenshot(path=str(OUT / "verified-recovery.png"), full_page=True)
        checks.append("repair does not resolve low-margin incident; extra simulated delivery and fresh readings verify recovery")

        page.get_by_role("button", name="Add a demo reading").click()
        page.get_by_role("button", name="Save demo reading").click()
        expect(page.locator("dialog")).not_to_be_visible()
        expect(page.locator(".source-label")).to_contain_text("Manual demo")
        checks.append("manual simulated reading advances virtual clock and persists")
        page.get_by_role("button", name="Evidence & evaluation", exact=True).click()
        expect(page.locator(".artifact-values")).to_contain_text("149.1")
        page.screenshot(path=str(OUT / "evaluation.png"), full_page=True)
        checks.append("evaluation page renders generated artifact")

        page.get_by_role("button", name="Overview", exact=True).click()
        page.get_by_role("button", name="Reset demo", exact=True).click()
        page.locator("dialog").get_by_role("button", name="Reset demo", exact=True).click()
        expect(page.locator(".tank-copy h2")).to_contain_text("32,000")
        checks.append("reset restores isolated healthy demo")
        mobile_context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=1)
        mobile = mobile_context.new_page()
        mobile.on("pageerror", lambda error: errors.append(str(error)))
        mobile.goto(url)
        expect(mobile.locator(".tank-copy h2")).to_contain_text("32,000")
        overflow = mobile.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        assert not overflow, "Mobile horizontal overflow"
        mobile.screenshot(path=str(OUT / "mobile.png"), full_page=True)
        checks.append("390px mobile viewport has no horizontal overflow")

        mobile.get_by_role("button", name="Add a demo reading").click()
        mobile.locator("#volume").fill("36000")
        mobile.get_by_role("button", name="Save demo reading").click()
        expect(mobile.get_by_text("More evidence needed", exact=True)).to_be_visible()
        expect(mobile.get_by_role("button", name="Review supply request")).to_be_disabled()
        mobile.get_by_role("button", name="What if supply is six hours late?").click()
        expect(mobile.locator(".assistant-answer")).to_contain_text("unknown")
        mobile.screenshot(path=str(OUT / "unknown-mobile.png"), full_page=True)
        checks.append("unknown inflow produces UNKNOWN, disables proposal and preserves truthful assistant fallback")

        offline = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
        offline.route("**/api/dashboard", lambda route: route.abort())
        offline.goto(url)
        expect(offline.get_by_role("button", name="Reconnect", exact=True)).to_be_visible(timeout=25000)
        assert offline.locator(".tank-card").count() == 0
        checks.append("API failure shows reconnect, with no invented tank values")
        assert not errors, errors
        browser.close()
    report = {"status": "PASS", "checked_at_utc": datetime.now(UTC).isoformat(), "tool": "Playwright / Chromium", "url": url, "checks": checks, "unexpected_page_errors": errors, "screenshots": sorted(path.name for path in OUT.glob("*.png")), "limits": "Local simulated prototype only; no AWS, external recipient or real sensor verification."}
    (ROOT / "artifacts/browser-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000")
