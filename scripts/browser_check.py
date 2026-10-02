"""Check the built UI in Chromium; generated E2E inputs are not field logs."""
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/screenshots"


def run(url="http://127.0.0.1:8000"):
    OUT.mkdir(parents=True, exist_ok=True)
    checks, errors, screenshots, observations = [], [], [], {}
    failure = None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        # One cookie session avoids incidental per-IP session-creation quota.
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1, accept_downloads=True)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))

        def capture(name):
            page.evaluate("window.scrollTo(0, 0)")
            page.screenshot(path=str(OUT / name), full_page=True)
            screenshots.append(name)

        def dashboard():
            response = context.request.get(url + "/api/dashboard")
            assert response.ok, f"Dashboard HTTP {response.status}: {response.text()}"
            return response.json()

        def click_api(locator, endpoint):
            with page.expect_response(lambda response: response.url.endswith("/api" + endpoint) and response.request.method == "POST") as pending:
                locator.click()
            response = pending.value
            assert response.ok, f"{endpoint} HTTP {response.status}: {response.text()}"
            return response.json()

        def formatted(value, fractional=False):
            return page.evaluate("([v, f]) => v === null ? '—' : new Intl.NumberFormat('en-IN', {maximumFractionDigits: f ? 1 : 0}).format(v)", [value, fractional])

        def assert_volume(value):
            expect(page.locator(".tank-copy h2")).to_contain_text(formatted(value), timeout=20000)

        def no_overflow():
            assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), "Horizontal viewport overflow"

        try:
            with page.expect_response(lambda response: response.url.endswith("/api/dashboard")) as initial_response:
                page.goto(url)
            initial = initial_response.value.json()
            assert initial["mode"] == "SIMULATED_DEMO"
            assert_volume(initial["state"]["volume_l"])
            expect(page.get_by_text("SIMULATED DEMO", exact=True)).to_be_visible()
            capture("desktop.png")
            page.screenshot(path=str(OUT / "desktop-preview.png"), full_page=False)
            screenshots.append("desktop-preview.png")
            checks.append("Initial demo storage and status render API-backed state without fallback values")

            page.get_by_role("button", name="What if?", exact=True).click()
            page.locator("#delay").fill("24")
            preview = click_api(page.get_by_role("button", name="Compare this plan"), "/simulate")
            expect(page.locator(".preview-result")).to_be_visible()
            expect(page.locator(".preview-metrics")).to_contain_text(formatted(preview["analysis"]["shortage_hours"], True) + " hours")
            assert preview["analysis"]["current_rate_lph"] == initial["analysis"]["current_rate_lph"], "Preview changed the observed interval rate"
            assert dashboard()["version"] == initial["version"], "Preview mutated evidence"
            observations["24h_delay_shortage_hours_from_api"] = preview["analysis"]["shortage_hours"]
            capture("scenario-preview.png")
            page.get_by_role("button", name="Close dialog").click()
            checks.append("24-hour preview matches API shortage, preserves observed rate, and does not mutate evidence")

            answer = click_api(page.get_by_role("button", name="Why is this the action deadline?"), "/assistant")
            assert answer["provider"] == "deterministic" and answer["simulated"] is True
            expect(page.locator(".assistant-answer")).to_contain_text("observed-demand planning envelope")
            checks.append("Deterministic guide explains observed-demand planning assumptions without a safety guarantee")

            excess = click_api(page.get_by_role("button", name="Excess usage", exact=True), "/demo/scenario")
            assert_volume(excess["state"]["volume_l"])
            assert excess["analysis"]["anomaly"]["active"] and excess["incident"]
            expect(page.get_by_text("Action needed now", exact=True)).to_be_visible()
            capture("excess-usage.png")
            checks.append("Excess-use scenario updates observed evidence, risk and incident through the server")

            click_api(page.get_by_role("button", name="Review supply request"), "/actions/propose")
            approve = page.get_by_role("button", name="Approve demo request")
            expect(approve).to_be_disabled()
            expect(page.locator("dialog").get_by_role("checkbox")).not_to_be_checked()
            page.locator("dialog").get_by_role("checkbox").check()
            expect(approve).to_be_enabled()
            capture("approval.png")
            with page.expect_response(lambda response: "/approve" in response.url and response.request.method == "POST") as approval_response:
                approve.click()
            approved = approval_response.value.json()
            assert approved["actions"][-1]["status"] == "LOCAL_RECEIVED"
            expect(page.locator(".receipt-strip")).to_contain_text("Local received")
            checks.append("Approval starts unchecked and creates a local receipt, not a supplier booking")

            repaired = click_api(page.get_by_role("button", name="Repair + readings"), "/demo/scenario")
            if repaired["incident"]["status"] == "RESOLVED":
                assert repaired["incident"]["verification_count"] >= 3 and repaired["incident"]["verified_at"]
                expect(page.locator(".incident-card")).to_contain_text("Resolved")
            else:
                expect(page.locator(".incident-card")).to_contain_text("Verifying")
            observations["repair_scenario_incident_status"] = repaired["incident"]["status"]
            capture("verified-recovery.png")
            checks.append("Repair follows current server evidence; resolution requires at least three accepted verification readings")

            page.get_by_role("button", name="Add a demo reading").click()
            expect(page.locator("dialog")).to_contain_text("advances the demo clock by 30 minutes")
            manual_demo = click_api(page.get_by_role("button", name="Save demo reading"), "/readings")
            expect(page.locator("dialog")).not_to_be_visible()
            assert manual_demo["state"]["source"] == "manual_demo" and manual_demo["state"]["simulated"]
            expect(page.locator(".source-label")).to_contain_text("Manual demo")
            checks.append("Manual demo entry discloses clock advance and remains simulated")

            page.get_by_role("button", name="Evidence & evaluation", exact=True).click()
            evaluation = manual_demo["evaluation"]
            expect(page.locator(".evaluation-results")).to_contain_text(formatted(evaluation["final_test"]["recent_mean_selected"]["mae_l"], True))
            expect(page.locator(".evaluation-results")).to_contain_text("Legacy")
            stress_cases = evaluation["reserve_timing"]["stress"]["cases"]
            stress_failures = sum(case["upgraded"]["all_windows"]["late_event_predictions"] > 0 or case["upgraded"]["all_windows"]["missed_horizon_events"] > 0 for case in stress_cases)
            expect(page.locator(".reserve-evaluation")).to_contain_text(f"{stress_failures} / {len(stress_cases)}")
            expect(page.locator(".reserve-evaluation")).to_contain_text("not a safety guarantee")
            expect(page.locator(".reserve-evaluation")).to_contain_text("Already-passed predicted action deadlines")
            observations["stress_failure_cases_from_artifact"] = stress_failures
            capture("evaluation.png")
            checks.append("Evaluation separates actual legacy demand metrics from reserve timing, stress failures and passed deadlines")

            page.get_by_role("button", name="Overview", exact=True).click()
            page.get_by_role("button", name="Reset demo", exact=True).click()
            reset = click_api(page.locator("dialog").get_by_role("button", name="Reset demo", exact=True), "/demo/reset")
            assert_volume(reset["state"]["volume_l"])
            page.set_viewport_size({"width": 390, "height": 844})
            no_overflow()
            capture("mobile.png")
            checks.append("390px demo overview has no horizontal overflow")
            page.get_by_role("button", name="Add a demo reading").click()
            page.locator("#volume").fill(str(reset["state"]["volume_l"] + 4000))
            unknown = click_api(page.get_by_role("button", name="Save demo reading"), "/readings")
            assert unknown["analysis"]["status"] == "UNKNOWN"
            expect(page.get_by_text("More evidence needed", exact=True)).to_be_visible()
            expect(page.get_by_role("button", name="Review supply request")).to_be_disabled()
            click_api(page.get_by_role("button", name="What if supply is six hours late?"), "/assistant")
            expect(page.locator(".assistant-answer")).to_contain_text(re.compile("unknown", re.I))
            capture("unknown-mobile.png")
            checks.append("Unrecorded inflow is UNKNOWN, blocks proposals, and preserves truthful assistant fallback")
            page.get_by_role("button", name="Reset demo", exact=True).click()
            click_api(page.locator("dialog").get_by_role("button", name="Reset demo", exact=True), "/demo/reset")
            page.set_viewport_size({"width": 1440, "height": 1000})

            page.get_by_role("button", name="Data & settings", exact=True).first.click()
            open_workspace = page.get_by_role("button", name="Open empty observed workspace")
            expect(open_workspace).to_be_disabled()
            expect(page.locator(".workspace-confirmation input")).not_to_be_checked()
            page.get_by_label("Tank / site name").fill("GENERATED E2E TEST TANK — NOT FIELD DATA")
            page.get_by_label("Supply lead time · hours").fill("4")
            page.get_by_label("Planning buffer · hours").fill("2")
            page.get_by_label("Reading error assumption · litres").fill("10")
            page.locator(".workspace-confirmation input").check()
            live = click_api(open_workspace, "/workspace/live")
            assert live["mode"] == "LOCAL_OBSERVED" and live["state"]["volume_l"] is None
            assert live["state"]["percentage"] is None and live["analysis"]["status"] == "UNKNOWN"
            assert live["analysis"]["history"] == [] and live["state"]["simulated"] is False
            page.get_by_role("button", name="Overview", exact=True).click()
            expect(page.locator(".tank-copy h2")).to_contain_text("No reading yet")
            expect(page.locator(".tank-illustration")).to_contain_text("NO OBSERVATION")
            assert page.get_by_role("button", name="Excess usage", exact=True).count() == 0
            expect(page.get_by_role("button", name="Review supply request")).to_be_disabled()
            expect(page.get_by_role("button", name="Record inspection note", exact=True)).to_be_disabled()
            capture("local-empty.png")
            checks.append("Observed transition needs explicit consent, clears demo history, starts null/UNKNOWN and hides demo controls")

            page.get_by_role("button", name="Add first observation").click()
            expect(page.locator("#volume")).to_have_value("")
            expect(page.locator(".observation-time input")).to_be_editable()
            expect(page.locator("dialog")).to_contain_text("operator-entered evidence")
            page.get_by_role("button", name="Cancel", exact=True).click()
            checks.append("Actual observation form starts blank with an editable IST observation time")

            current = dashboard()
            anchor = datetime.fromisoformat(current["clock"]).astimezone(UTC).replace(second=0, microsecond=0) - timedelta(minutes=2)
            run_id = anchor.strftime("%Y%m%d%H%M")
            readings = []
            for index in range(9):
                at = anchor - timedelta(hours=8 - index)
                volume = 32000 - 1000 * index + (5000 if index >= 5 else 0)
                readings.append({"reading_id": f"generated-e2e-{run_id}-{index}", "observed_at": at.isoformat(), "volume_l": volume})
            arrived = {"id": f"generated-e2e-arrival-{run_id}", "arrived_at": (anchor - timedelta(hours=3)).isoformat(), "amount_l": 5000}
            csv_text = "reading_id,observed_at,volume_l\n" + "\n".join(f"{row['reading_id']},{row['observed_at']},{row['volume_l']}" for row in readings)
            page.get_by_role("button", name="Data & settings", exact=True).first.click()
            page.get_by_label("Observations CSV", exact=True).fill(csv_text)
            page.get_by_label("Optional recorded arrivals · JSON array").fill(json.dumps([arrived]))
            page.get_by_role("button", name="Preview logs").click()
            expect(page.locator(".import-preview")).to_contain_text("9 observations · 1 recorded arrivals")
            imported = click_api(page.get_by_role("button", name="Import these records"), "/import")
            assert imported["state"]["volume_l"] == readings[-1]["volume_l"]
            assert imported["state"]["source"] == "manual_observed" and imported["state"]["simulated"] is False
            assert imported["analysis"]["current_rate_lph"] == 1000, "Recorded arrival was miscounted as consumption or tank volume"
            assert all(point["rate_lph"] in (None, 1000) for point in imported["analysis"]["history"])
            expect(page.locator(".data-workspace")).to_contain_text("complete import was accepted")
            checks.append("Generated E2E fixture imports logs and arrivals atomically with correct inflow-adjusted demand")

            page.get_by_label("Observations CSV", exact=True).fill("wrong,columns\n1,2")
            page.get_by_role("button", name="Preview logs").click()
            expect(page.locator(".data-workspace [role=alert]")).to_contain_text("requires observed_at and volume_l")
            expect(page.get_by_role("button", name="Import these records")).to_be_disabled()
            assert dashboard()["version"] == imported["version"]
            checks.append("Malformed CSV is visibly rejected without creating observations")

            conflicting_csv = "reading_id,observed_at,volume_l\n" + f"{readings[0]['reading_id']},{readings[0]['observed_at']},{readings[0]['volume_l'] + 1}"
            page.get_by_label("Observations CSV", exact=True).fill(conflicting_csv)
            page.get_by_role("button", name="Preview logs").click()
            with page.expect_response(lambda response: response.url.endswith("/api/import")) as conflict_response:
                page.get_by_role("button", name="Import these records").click()
            assert conflict_response.value.status == 409
            expect(page.locator(".data-workspace [role=alert]")).to_be_visible()
            assert dashboard()["version"] == imported["version"]
            checks.append("Conflicting import returns visible server error and preserves prior evidence")

            page.get_by_label("Observations CSV", exact=True).fill("")
            page.get_by_label("Supply record type").select_option("planned")
            scheduled = anchor + timedelta(hours=10)
            page.get_by_label("Scheduled time · IST").fill((scheduled + timedelta(minutes=330)).strftime("%Y-%m-%dT%H:%M"))
            page.get_by_label("Volume · litres", exact=True).fill("12000")
            planned = click_api(page.get_by_role("button", name="Save supply plan"), "/deliveries")
            assert planned["state"]["volume_l"] == imported["state"]["volume_l"]
            assert planned["analysis"]["next_supply_at"]
            expect(page.locator(".data-workspace")).to_contain_text("not recorded as arrived water")
            checks.append("Planned supply is conditional and does not increase measured tank volume")

            page.get_by_label("Planning buffer · hours").fill("3")
            page.get_by_label("Supply lead time · hours").fill("10")
            configured = click_api(page.get_by_role("button", name="Save tank settings"), "/site")
            assert configured["site"]["lead_hours"] == 10 and configured["site"]["buffer_hours"] == 3
            assert configured["state"]["volume_l"] == imported["state"]["volume_l"]
            assert configured["version"] > planned["version"]
            checks.append("Editable tank settings recompute forecasts and retain stored observations")

            page.get_by_role("button", name="Overview", exact=True).click()
            page.get_by_role("button", name="Add observation", exact=True).click()
            expect(page.locator("#volume")).to_have_value("")
            observed_at = anchor + timedelta(minutes=1)
            page.locator(".observation-time input").fill((observed_at + timedelta(minutes=330)).strftime("%Y-%m-%dT%H:%M"))
            page.locator("#volume").fill("28983")
            actual = click_api(page.get_by_role("button", name="Save observation", exact=True), "/readings")
            assert actual["state"]["source"] == "manual_observed" and actual["state"]["simulated"] is False
            assert actual["state"]["volume_l"] == 28983
            assert datetime.fromisoformat(actual["state"]["observed_at"]) == observed_at
            assert abs((datetime.fromisoformat(actual["clock"]) - datetime.now(UTC)).total_seconds()) < 60
            expect(page.locator(".source-label")).to_contain_text("Operator-entered · unverified")
            expect(page.locator(".scenario-lab")).to_have_count(0)
            page.locator(".forecast-explanation > summary").click()
            expect(page.locator(".forecast-explanation")).to_contain_text("not sensor certification")
            expect(page.locator(".forecast-explanation")).to_contain_text("supporting history")
            capture("local-observed.png")
            checks.append("Manual entry saves exact timestamp without advancing wall clock; provenance and assumptions remain explicit")

            page.get_by_role("button", name="Data & settings", exact=True).first.click()
            expect(page.locator(".backup-card")).to_contain_text("30 days")
            with page.expect_download() as download_pending:
                page.get_by_role("button", name="Download JSON backup").click()
            with TemporaryDirectory(prefix="jalrakshak-e2e-export-") as temporary:
                backup_path = Path(temporary) / "backup.json"
                download_pending.value.save_as(backup_path)
                backup = json.loads(backup_path.read_text(encoding="utf-8"))
            assert backup["mode"] == "LOCAL_OBSERVED" and len(backup["readings"]) == 10
            assert len(backup["deliveries"]) == 2 and backup["schema_version"]
            forbidden_keys = {"csrf_token", "session_id", "jal_session", "cookie", "cookies", "authorization"}

            def inspect_keys(value):
                if isinstance(value, dict):
                    assert not forbidden_keys.intersection(key.lower() for key in value), "Export leaked session credentials"
                    for child in value.values():
                        inspect_keys(child)
                elif isinstance(value, list):
                    for child in value:
                        inspect_keys(child)

            inspect_keys(backup)
            checks.append("Browser downloads backup with evidence/settings, excluding credentials; retention limits remain visible")

            page.set_viewport_size({"width": 390, "height": 844})
            no_overflow()
            capture("local-data-mobile.png")
            page.get_by_role("button", name="Overview", exact=True).click()
            no_overflow()
            capture("local-observed-mobile.png")
            checks.append("390px observed overview and settings/import/export forms have no horizontal overflow")

            page.get_by_role("button", name="Evidence & evaluation", exact=True).click()
            expect(page.locator(".evidence-intro")).to_contain_text("not evaluation of the actual logs")
            no_overflow()
            checks.append("Observed workspace keeps synthetic evaluation separate; artifact tables remain responsive")
            page.get_by_role("button", name="Overview", exact=True).click()

            # Coherent mocked stale response exercises the actual browser timer.
            # Backend tests independently verify real clock/domain freshness.
            stale = deepcopy(actual)
            stale["clock"] = (datetime.fromisoformat(actual["clock"]) + timedelta(hours=2)).isoformat()
            stale["state"]["data_state"] = "stale"
            stale["analysis"].update(status="UNKNOWN", current_rate_lph=None, latest_action_at=None, action_margin_hours=None, hours_to_reserve=None, reserve_breach_at=None, conservative_breach_at=None, empty_at=None, projection=[], shortage_hours=None, unmet_demand_l=None, overflow_l=None)
            stale["analysis"]["anomaly"].update(active=False, observed_rate_lph=None, ratio=None, evidence_count=0, reason="Generated stale-observation UI test")
            stale["analysis"]["recommendation"] = {"type": "READ_TANK", "title": "Generated stale-response UI test", "body": "Record a fresh observation.", "deadline": None}
            page.route("**/api/dashboard", lambda route: route.fulfill(json=stale))
            expect(page.get_by_text("More evidence needed", exact=True)).to_be_visible(timeout=35000)
            expect(page.get_by_role("button", name="Review supply request")).to_be_disabled()
            expect(page.locator(".tank-mini-stats")).to_contain_text("Stale")
            assert_volume(actual["state"]["volume_l"])
            capture("local-stale-mobile.png")
            page.unroute("**/api/dashboard")
            checks.append("Actual 30-second timer accepts mocked stale-clock response, blocks proposals and preserves measured volume")

            page.route("**/api/dashboard", lambda route: route.abort())
            page.get_by_role("button", name="Refresh dashboard", exact=True).click()
            expect(page.get_by_text("Automatic refresh failed.", exact=False)).to_be_visible(timeout=25000)
            assert_volume(actual["state"]["volume_l"])
            page.unroute("**/api/dashboard")
            checks.append("Refresh failure visibly preserves last-known data without invented current values")

            offline = context.new_page()
            offline.on("pageerror", lambda error: errors.append(str(error)))
            offline.route("**/api/dashboard", lambda route: route.abort())
            offline.goto(url)
            expect(offline.get_by_role("button", name="Reconnect", exact=True)).to_be_visible(timeout=25000)
            assert offline.locator(".tank-card").count() == 0
            checks.append("Initial API failure shows reconnect without fabricated readings or metrics")
            assert not errors, errors
        except Exception as error:
            failure = f"{type(error).__name__}: {error}"
            try:
                capture("browser-failure.png")
            except Exception:
                pass
        finally:
            browser.close()

    report = {"status": "FAIL" if failure else "PASS", "checked_at_utc": datetime.now(UTC).isoformat(), "tool": "Playwright / Chromium", "url": url, "checks": checks, "unexpected_page_errors": errors, "failure": failure, "screenshots": screenshots, "observations": observations, "test_inputs": {"label": "GENERATED E2E TEST INPUTS — NOT FIELD OBSERVATIONS", "purpose": "Generated E2E numbers and recent timestamps exercise observed ingestion; these are not field logs or field deployment evidence.", "generated_readings": 9, "generated_arrivals": 1, "browser_sessions": 1}, "limits": "Local browser and HTTP integration only. No AWS execution, external recipient, calibrated sensor or field accuracy claim. Stale browser polling uses an explicitly mocked dashboard snapshot; actual clock/domain freshness is tested separately."}
    (ROOT / "artifacts/browser-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000")
