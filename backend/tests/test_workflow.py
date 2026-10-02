"""Exercise approval, persistence and recovery through the actual HTTP boundary."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.operations import parse, iso
from backend.app.repository import SQLiteRepository


@pytest.fixture
def repository(tmp_path):
    return SQLiteRepository(str(tmp_path / "sessions.sqlite3"))


@pytest.fixture
def client(repository):
    return TestClient(create_app(repository))


def start(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    dashboard = response.json()
    client.headers["X-CSRF-Token"] = dashboard["csrf_token"]
    return dashboard


def post(client, path, body):
    response = client.post("/api" + path, json=body)
    assert response.status_code == 200, response.text
    return response.json()


def excess(client):
    return post(client, "/demo/scenario", {"scenario": "excess_usage", "hours": 2})


def test_complete_incident_loop_requires_approval_and_fresh_recovery(client):
    initial = start(client)
    assert initial["analysis"]["status"] == "SAFE"
    assert initial["state"]["volume_l"] == 32000
    assert initial["incident"] is None
    danger = excess(client)
    assert danger["analysis"]["status"] == "ACT_NOW"
    assert danger["analysis"]["anomaly"]["active"] is True
    assert danger["incident"]["status"] == "OPEN"
    action = post(client, "/actions/propose", {"type": "REQUEST_SUPPLY"})
    assert action["status"] == "PROPOSED"
    assert action["receipt_at"] is None
    refused = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": False})
    assert refused.status_code == 409
    approved = post(client, f"/actions/{action['id']}/approve", {"evidence_version": action["evidence_version"], "confirmed": True})
    assert approved["actions"][-1]["status"] == "LOCAL_RECEIVED"
    assert approved["actions"][-1]["receipt_at"] is not None
    assert approved["actions"][-1]["published_at"] is None
    assert approved["incident"]["status"] == "ACTION_REQUESTED"
    claimed = post(client, "/interventions", {"note": "Pipe inspected"})
    assert claimed["incident"]["status"] == "VERIFYING"
    assert claimed["incident"]["verified_at"] is None
    assert claimed["incident"]["verification_count"] == 0
    repaired = post(client, "/demo/scenario", {"scenario": "repair"})
    assert repaired["analysis"]["anomaly"]["active"] is False
    assert repaired["incident"]["status"] == "VERIFYING"  # Margin is still inadequate.
    delivered = post(client, "/demo/scenario", {"scenario": "delivery"})
    assert delivered["analysis"]["status"] == "SAFE"
    assert delivered["incident"]["status"] == "RESOLVED"
    assert delivered["incident"]["verification_count"] >= 3
    assert "Physical repair is not verified" in delivered["incident"]["reason"]
    assert len([event for event in delivered["events"] if event["kind"] == "VERIFIED"]) == 1


def test_simulation_is_read_only_and_planned_supply_is_conditional(client):
    initial = start(client)
    preview = post(client, "/simulate", {"delay_hours": 24, "added_supply_l": 10000, "demand_change_percent": 0})
    assert preview["simulated"] is True
    assert preview["analysis"]["latest_action_at"] == initial["analysis"]["latest_action_at"]
    after = client.get("/api/dashboard").json()
    assert after == initial


@pytest.mark.parametrize("change", [-50, 50, 100])
def test_demand_sensitivity_keeps_valid_anchor_and_changes_demand(client, change):
    initial = start(client)
    preview = post(client, "/simulate", {"delay_hours": 0, "demand_change_percent": change})
    assert preview["analysis"]["status"] != "UNKNOWN"
    assert preview["analysis"]["current_rate_lph"] == pytest.approx(960 * (1 + change / 100))
    assert preview["analysis"]["projection"][0]["volume_l"] == initial["state"]["volume_l"]
    assert client.get("/api/dashboard").json() == initial


def test_stale_proposal_cannot_be_approved(client):
    start(client)
    action = post(client, "/actions/propose", {})
    excess(client)
    response = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": True})
    assert response.status_code == 409
    assert "Evidence changed" in response.json()["detail"]
    assert client.get("/api/dashboard").json()["actions"][0]["status"] == "PROPOSED"


def test_delivery_does_not_silently_repair_excess_use(client):
    start(client)
    excess(client)
    delivered = post(client, "/demo/scenario", {"scenario": "delivery"})
    assert delivered["analysis"]["current_rate_lph"] == 2400
    assert delivered["analysis"]["anomaly"]["active"] is True
    assert delivered["incident"]["status"] == "VERIFYING"
    assert delivered["incident"]["verified_at"] is None


def test_approval_refuses_evidence_that_became_unknown_before_expiry(client, repository):
    initial = start(client)
    session = client.cookies.get("jal_session")
    repository.mutate(session, lambda context: context.update(clock=iso(parse(initial["clock"]) + timedelta(hours=1))))
    action = post(client, "/actions/propose", {})
    repository.mutate(session, lambda context: context.update(clock=iso(parse(initial["clock"]) + timedelta(minutes=105))))
    assert client.get("/api/dashboard").json()["analysis"]["status"] == "UNKNOWN"
    response = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": True})
    assert response.status_code == 409
    assert "Fresh usable evidence" in response.json()["detail"]


def test_expired_proposal_rejected_even_with_unchanged_version(client, repository):
    initial = start(client)
    action = post(client, "/actions/propose", {})
    repository.mutate(client.cookies.get("jal_session"), lambda context: context.update(clock=iso(parse(initial["clock"]) + timedelta(hours=2))))
    response = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": True})
    assert response.status_code == 409
    assert "expired" in response.json()["detail"]


def test_session_isolation_and_sqlite_survives_app_restart(client, repository):
    start(client)
    danger = excess(client)
    other = TestClient(create_app(repository))
    assert start(other)["analysis"]["status"] == "SAFE"
    action = post(client, "/actions/propose", {})
    unauthorized = other.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": True})
    assert unauthorized.status_code == 404
    restarted = TestClient(create_app(SQLiteRepository(repository.path)))
    restarted.cookies.update(client.cookies)
    assert restarted.get("/api/dashboard").json()["incident"]["id"] == danger["incident"]["id"]


def test_csrf_and_origin_are_enforced(client):
    initial = start(client)
    client.headers.pop("X-CSRF-Token")
    assert client.post("/api/demo/reset", json={}).status_code == 403
    client.headers["X-CSRF-Token"] = "bad"
    assert client.post("/api/demo/reset", json={}).status_code == 403
    client.headers["X-CSRF-Token"] = initial["csrf_token"]
    client.headers["Origin"] = "https://untrusted.example"
    assert client.post("/api/demo/reset", json={}).status_code == 403
    client.headers["Origin"] = "http://localhost:5173"
    assert client.post("/api/demo/reset", json={}).status_code == 200
    stranger = TestClient(create_app(client.app.state.repository))
    assert stranger.post("/api/demo/reset", json={}).status_code == 401


def test_unknown_data_refuses_proposal_and_returns_null_metrics(client, repository):
    initial = start(client)
    repository.mutate(client.cookies.get("jal_session"), lambda context: context.update(clock=iso(parse(initial["clock"]) + timedelta(hours=3))))
    unknown = client.get("/api/dashboard").json()
    assert unknown["analysis"]["status"] == "UNKNOWN"
    assert unknown["analysis"]["unmet_demand_l"] is None
    assert client.post("/api/actions/propose", json={}).status_code == 409
    answer = post(client, "/assistant", {"question": "delay"})
    assert "unknown" in answer["answer"]


def test_repeated_reading_is_idempotent_conflicts_and_future_rejected(client):
    initial = start(client)
    # Before the seeded 24,000 L arrival: 8,960 - 480 = 8,480 L.
    reading = {"reading_id": "manual-id", "observed_at": iso(parse(initial["clock"]) - timedelta(minutes=30)), "volume_l": 8480, "source": "manual_demo", "simulated": True}
    first = post(client, "/readings", reading)
    assert post(client, "/readings", reading) == first
    assert client.post("/api/readings", json={**reading, "volume_l": 32481}).status_code == 409
    future = {**reading, "reading_id": "future", "observed_at": iso(parse(initial["clock"]) + timedelta(milliseconds=500))}
    assert client.post("/api/readings", json=future).status_code == 409
    conflicting_time = {**reading, "reading_id": "same-time-conflict", "observed_at": initial["clock"], "volume_l": 31000}
    assert client.post("/api/readings", json=conflicting_time).status_code == 409
    assert client.get("/api/dashboard").json()["analysis"]["status"] != "UNKNOWN"


def test_explicit_demo_manual_clock_advance_is_bounded_and_idempotent(client):
    initial = start(client)
    reading = {"reading_id": "advanced-demo", "observed_at": iso(parse(initial["clock"]) + timedelta(minutes=30)), "volume_l": 31520, "source": "manual_demo", "simulated": True, "advance_clock": True}
    saved = post(client, "/readings", reading)
    assert saved["clock"] == reading["observed_at"]
    assert saved["state"]["source"] == "manual_demo"
    assert saved["analysis"]["current_rate_lph"] == 960
    assert post(client, "/readings", reading) == saved
    invalid = {**reading, "reading_id": "far-future", "observed_at": iso(parse(saved["clock"]) + timedelta(hours=4))}
    assert client.post("/api/readings", json=invalid).status_code == 409
    assert client.get("/api/dashboard").json() == saved


@pytest.mark.parametrize("count", [2, 3])
def test_late_reading_invalidates_prior_verification_even_after_resolution(count):
    from backend.app import operations
    context = operations.seed()
    operations.scenario(context, "excess_usage", 2)
    operations.record_intervention(context, "Simulated inspection")
    anchor = parse(context["clock"])
    context["deliveries"].append({"id": "test-arrival", "scheduled_at": iso(anchor + timedelta(minutes=30)), "arrived_at": iso(anchor + timedelta(minutes=30)), "amount_l": 18000, "status": "ARRIVED"})
    volume = 45200
    for number in range(1, count + 1):
        at = anchor + timedelta(minutes=30 * number)
        volume -= 480
        context["clock"] = iso(at)
        operations.ingest(context, {"reading_id": f"recovery-{number}", "observed_at": iso(at), "volume_l": volume, "source": "manual_demo", "simulated": True})
    assert context["incident"]["verification_count"] == count
    if count == 3:
        assert context["incident"]["status"] == "RESOLVED"
    operations.ingest(context, {"reading_id": "late-revision", "observed_at": iso(anchor + timedelta(minutes=15)), "volume_l": 26000, "source": "manual_demo", "simulated": True})
    assert context["incident"]["verification_count"] == 0
    assert context["incident"]["verified_at"] is None
    assert context["incident"]["status"] == "VERIFYING"
    at = parse(context["clock"]) + timedelta(minutes=30)
    context["clock"] = iso(at)
    operations.ingest(context, {"reading_id": "one-new-normal", "observed_at": iso(at), "volume_l": volume - 480, "source": "manual_demo", "simulated": True})
    assert context["incident"]["status"] != "RESOLVED"
    assert context["incident"]["verification_count"] == 1


def test_unknown_observation_resets_recovery_batch():
    from backend.app import operations
    context = operations.seed()
    operations.scenario(context, "excess_usage", 2)
    operations.scenario(context, "repair", 2)
    operations.scenario(context, "delivery", 2)
    # Begin another explicit verification batch after prior simulated recovery.
    operations.record_intervention(context, "Rechecking")
    context["incident"].update(status="VERIFYING", intervention_at=context["clock"], verification_count=2, verification_reading_ids=["earlier-1", "earlier-2"])
    at = parse(context["clock"]) + timedelta(minutes=30)
    context["clock"] = iso(at)
    last_volume = context["readings"][-1]["volume_l"]
    operations.ingest(context, {"reading_id": "unknown-inflow", "observed_at": iso(at), "volume_l": last_volume + 100, "source": "manual_demo", "simulated": True})
    assert context["incident"]["status"] == "UNKNOWN"
    assert context["incident"]["verification_count"] == 0
    assert context["incident"]["verification_reading_ids"] == []


@pytest.mark.parametrize("changes", [{"volume_l": -1}, {"volume_l": 50001}, {"simulated": False}, {"source": "live_sensor"}, {"observed_at": "2026-10-01T04:30:00"}, {"unexpected": "anything"}])
def test_reading_schema_rejects_invalid_and_real_site_claims(client, changes):
    initial = start(client)
    reading = {"reading_id": "test", "observed_at": initial["clock"], "volume_l": 32000, "source": "manual_demo", "simulated": True}
    assert client.post("/api/readings", json={**reading, **changes}).status_code == 422


@pytest.mark.parametrize("nonfinite", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_raw_request_is_rejected_without_server_error(client, nonfinite):
    initial = start(client)
    raw = '{"reading_id":"bad-number","observed_at":"' + initial["clock"] + '","volume_l":' + nonfinite + ',"source":"manual_demo","simulated":true}'
    response = client.post("/api/readings", content=raw, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert client.get("/api/dashboard").json() == initial


@pytest.mark.parametrize("coerced", ["yes", "true", 1])
def test_approval_requires_an_actual_json_boolean(client, coerced):
    start(client)
    action = post(client, "/actions/propose", {})
    response = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": coerced})
    assert response.status_code == 422
    assert client.get("/api/dashboard").json()["actions"][-1]["receipt_at"] is None


def test_repository_closes_connections_for_windows_portability(repository):
    from pathlib import Path
    from backend.app.operations import seed
    repository.create("resource-test", seed())
    assert repository.get("resource-test") is not None
    source = Path(repository.path)
    renamed = source.with_suffix(".moved")
    source.rename(renamed)  # Windows refuses this if a SQLite connection remains open.
    renamed.rename(source)


def test_duplicate_concurrent_approval_records_one_receipt_event(client, repository):
    start(client)
    action = post(client, "/actions/propose", {})
    session = client.cookies.get("jal_session")
    from backend.app.operations import approve
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: repository.mutate(session, lambda context: approve(context, action["id"], action["evidence_version"], True)), range(2)))
    assert all(result["actions"][-1]["status"] == "LOCAL_RECEIVED" for result in results)
    stored = repository.get(session)
    assert len([event for event in stored["events"] if event["kind"] == "NOTICE"]) == 1


def test_reset_only_own_session_and_assistant_is_grounded(client, repository):
    initial = start(client)
    danger = excess(client)
    answer = post(client, "/assistant", {"question": "deadline"})
    assert answer["provider"] == "deterministic"
    assert danger["analysis"]["latest_action_at"] in answer["answer"]
    assert answer["facts"] == danger["analysis"]["facts"]
    reset = post(client, "/demo/reset", {})
    assert reset["csrf_token"] == initial["csrf_token"]
    assert reset["incident"] is None
    assert reset["actions"] == []
    assert reset["analysis"]["status"] == "SAFE"
