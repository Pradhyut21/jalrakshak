"""Actual local-record behavior at the HTTP boundary; all test data is synthetic."""
from datetime import UTC, datetime, timedelta
import json

import pytest
from fastapi.testclient import TestClient

from backend.app import operations
from backend.app.main import create_app
from backend.app.repository import SQLiteRepository


NOW = datetime(2026, 10, 2, 12, tzinfo=UTC)
SETTINGS = {"name": "Test operator tank", "capacity_l": 50000, "reserve_l": 5000,
            "lead_hours": 14, "buffer_hours": 3, "measurement_error_l": 1,
            "measurement_error_basis": "GENERATED TEST FIXTURE: a declared synthetic bound; no field calibration.",
            "time_zone": "UTC"}


@pytest.fixture
def local(monkeypatch, tmp_path):
    clock = {"now": NOW}
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock["now"].astimezone(tz) if tz is not None else clock["now"].replace(tzinfo=None)
    monkeypatch.setattr(operations, "datetime", Clock)
    monkeypatch.setenv("JAL_DEMO_ONLY", "false")
    monkeypatch.setenv("JAL_COOKIE_SECURE", "false")
    repository = SQLiteRepository(str(tmp_path / "observed.sqlite3"))
    client = TestClient(create_app(repository))
    dashboard = client.get("/api/dashboard").json()
    client.headers["X-CSRF-Token"] = dashboard["csrf_token"]
    return client, repository, clock


def post(client, path, body):
    response = client.post("/api" + path, json=body)
    assert response.status_code == 200, response.text
    return response.json()


def observed(local, settings=None):
    client, _, _ = local
    return post(client, "/workspace/live", settings or SETTINGS)


def reading(at, volume, identity=None, **extra):
    return {"reading_id": identity or at.isoformat(), "observed_at": at.isoformat(),
            "volume_l": volume, "source": "manual_observed", "simulated": False, **extra}


def known_demand(client, now=NOW):
    rows = [reading(now - timedelta(hours=hour), 32000 + 1000 * hour) for hour in range(12, -1, -1)]
    return post(client, "/import", {"readings": rows})


def persisted(local):
    client, repository, _ = local
    return repository.get(client.cookies.get("jal_session"))


def test_observed_workspace_starts_empty_unknown_without_copying_demo(local):
    client, _, _ = local
    original = client.get("/api/dashboard").json()
    response = client.post("/api/workspace/live", json=SETTINGS)
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["mode"] == "LOCAL_OBSERVED"
    assert dashboard["clock"] == NOW.isoformat()
    assert dashboard["state"]["volume_l"] is None
    assert dashboard["state"]["percentage"] is None
    assert dashboard["state"]["data_state"] == "insufficient"
    assert dashboard["analysis"]["status"] == "UNKNOWN"
    assert dashboard["analysis"]["shortage_hours"] is None
    assert dashboard["analysis"]["projection"] == []
    assert dashboard["deliveries"] == []
    assert persisted(local)["readings"] == []
    assert dashboard["incident"] is None and dashboard["actions"] == []
    assert dashboard["site"]["id"] != original["site"]["id"]
    assert dashboard["csrf_token"] == original["csrf_token"]
    assert dashboard["features"]["local_observed_mode"] is True
    assert "Max-Age=2592000" in response.headers["set-cookie"]


def test_actual_empty_tank_is_zero_measurement_not_missing_data_or_verified_shortage(local):
    observed(local)
    client, _, _ = local
    dashboard = post(client, "/readings", reading(NOW, 0, "empty-tank"))
    assert dashboard["state"]["volume_l"] == 0
    assert dashboard["state"]["percentage"] == 0
    assert dashboard["state"]["simulated"] is False
    assert dashboard["state"]["source"] == "manual_observed"
    assert dashboard["analysis"]["status"] == "UNKNOWN"  # One level is not a demand estimate.
    assert dashboard["analysis"]["unmet_demand_l"] is None
    assert client.post("/api/readings", json={}).status_code == 422


@pytest.mark.parametrize("change", [{"simulated": True}, {"source": "manual_demo"},
                                   {"advance_clock": True}, {"simulated": "false"},
                                   {"source": "synthetic_demo"}])
def test_observed_provenance_is_strict_and_cannot_advance_real_clock(local, change):
    observed(local)
    client, _, _ = local
    before = persisted(local)
    response = client.post("/api/readings", json={**reading(NOW, 32000), **change})
    assert response.status_code == 422
    assert persisted(local) == before


def test_observed_rejects_future_and_over_capacity_readings_atomically(local):
    observed(local)
    client, _, _ = local
    before = persisted(local)
    for row in (reading(NOW + timedelta(microseconds=1), 32000), reading(NOW, 50001)):
        assert client.post("/api/readings", json=row).status_code == 409
        assert persisted(local) == before


def test_observed_clock_moves_with_server_time_and_stale_data_cannot_be_approved(local):
    observed(local)
    client, _, clock = local
    latest = NOW - timedelta(minutes=60)
    post(client, "/import", {"readings": [reading(latest - timedelta(hours=1), 33000), reading(latest, 32000)]})
    action = post(client, "/actions/propose", {"type": "REQUEST_SUPPLY"})
    revision = action["evidence_version"]
    clock["now"] += timedelta(minutes=45)
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["clock"] == clock["now"].isoformat()
    assert dashboard["state"]["data_state"] == "stale"
    assert dashboard["analysis"]["status"] == "UNKNOWN"
    assert dashboard["version"] == revision
    response = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": revision, "confirmed": True})
    assert response.status_code == 409
    assert "Fresh usable evidence" in response.json()["detail"]
    assert persisted(local)["actions"][0]["receipt_at"] is None


def test_bad_import_rolls_back_prior_arrival_and_prior_valid_reading(local):
    observed(local)
    client, _, _ = local
    post(client, "/readings", reading(NOW, 9000, "existing"))
    before = persisted(local)
    response = client.post("/api/import", json={
        "deliveries": [{"id": "new-arrival", "amount_l": 3000, "arrived_at": (NOW - timedelta(hours=1)).isoformat()}],
        "readings": [reading(NOW - timedelta(hours=2), 30000, "valid-first"), reading(NOW, 9001, "existing")],
    })
    assert response.status_code == 409
    assert "different payload" in response.json()["detail"]
    assert persisted(local) == before
    assert client.post("/api/import", json={}).status_code == 409
    assert persisted(local) == before


def test_import_sorts_rows_preserves_provenance_and_identical_retry_does_not_revise_evidence(local):
    observed(local)
    client, _, _ = local
    body = {"readings": [reading(NOW, 32000, "latest"), reading(NOW - timedelta(hours=1), 33000, "earlier")]}
    first = post(client, "/import", body)
    before = persisted(local)
    again = post(client, "/import", body)
    assert first == again
    assert persisted(local) == before
    assert [row["reading_id"] for row in before["readings"]] == ["earlier", "latest"]
    assert all(row["simulated"] is False and row["source"] == "manual_observed" for row in before["readings"])
    assert first["analysis"]["current_rate_lph"] == 1000
    assert len([event for event in first["events"] if event["kind"] == "IMPORT"]) == 1


def test_arrival_updates_same_planned_id_then_counts_once_and_retries_are_idempotent(local):
    observed(local)
    client, _, _ = local
    post(client, "/import", {"readings": [reading(NOW - timedelta(hours=1), 20000), reading(NOW, 30000)]})
    assert client.get("/api/dashboard").json()["analysis"]["status"] == "UNKNOWN"
    post(client, "/deliveries", {"id": "truck-1", "amount_l": 12000, "scheduled_at": (NOW + timedelta(hours=1)).isoformat()})
    arrival = {"id": "truck-1", "amount_l": 11000, "arrived_at": NOW.isoformat()}
    result = post(client, "/deliveries", arrival)
    assert len(result["deliveries"]) == 1
    assert result["deliveries"][0]["status"] == "ARRIVED"
    assert result["analysis"]["current_rate_lph"] == 1000
    assert result["analysis"]["projection"][0]["volume_l"] == 30000
    next_hour = next(point for point in result["analysis"]["projection"] if point["at"] == (NOW + timedelta(hours=1)).isoformat())
    assert next_hour["volume_l"] == 29000
    before = persisted(local)
    assert post(client, "/deliveries", arrival) == result
    assert persisted(local) == before
    assert client.post("/api/deliveries", json={**arrival, "amount_l": 11001}).status_code == 409
    assert persisted(local) == before


@pytest.mark.parametrize("body, code", [
    ({"id": "bad", "amount_l": 1000}, 422),
    ({"id": "bad", "amount_l": 1000, "arrived_at": NOW.isoformat(), "scheduled_at": (NOW + timedelta(hours=1)).isoformat()}, 422),
    ({"id": "bad", "amount_l": 1000, "arrived_at": (NOW + timedelta(seconds=1)).isoformat()}, 409),
    ({"id": "bad", "amount_l": 1000, "scheduled_at": NOW.isoformat()}, 409),
])
def test_delivery_requires_unambiguous_and_physically_ordered_timestamp(local, body, code):
    observed(local)
    client, _, _ = local
    before = persisted(local)
    assert client.post("/api/deliveries", json=body).status_code == code
    assert persisted(local) == before


def test_site_settings_invalidate_old_approval_and_cannot_shrink_below_records(local):
    observed(local)
    client, _, _ = local
    known_demand(client)
    action = post(client, "/actions/propose", {"type": "REQUEST_INSPECTION"})
    assert "UNVERIFIED" in action["message"] and "SIMULATED DEMO" not in action["message"]
    updated = post(client, "/site", {**SETTINGS, "lead_hours": 18, "time_zone": "Asia/Kolkata"})
    assert updated["site"]["lead_hours"] == 18
    assert updated["site"]["time_zone"] == "Asia/Kolkata"
    assert updated["version"] > action["evidence_version"]
    refused = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": True})
    assert refused.status_code == 409
    assert "Evidence changed" in refused.json()["detail"]
    before = persisted(local)
    assert client.post("/api/site", json={**SETTINGS, "capacity_l": 40000}).status_code == 409
    assert persisted(local) == before


@pytest.mark.parametrize("settings", [{"reserve_l": 50000}, {"measurement_error_l": 50000},
                                      {"time_zone": "missing/timezone"}, {"name": "   "}, {"lead_hours": -1},
                                      {"lead_hours": 47, "buffer_hours": 2}])
def test_invalid_site_settings_cannot_destroy_observed_data(local, settings):
    observed(local)
    client, _, _ = local
    post(client, "/readings", reading(NOW, 32000))
    before = persisted(local)
    assert client.post("/api/site", json={**SETTINGS, **settings}).status_code == 422
    assert persisted(local) == before


def test_site_lead_and_buffer_exactly_equal_to_forecast_horizon_are_accepted(local):
    observed(local)
    client, _, _ = local
    result = post(client, "/site", {**SETTINGS, "lead_hours": 45, "buffer_hours": 3})
    assert result["site"]["lead_hours"] == 45
    assert result["site"]["buffer_hours"] == 3


def test_observed_records_block_demo_commands_and_second_workspace_replacement(local):
    observed(local)
    client, _, _ = local
    post(client, "/readings", reading(NOW, 32000))
    before = persisted(local)
    for path, body in (("/demo/reset", {}), ("/demo/scenario", {"scenario": "excess_usage"}),
                       ("/workspace/live", SETTINGS)):
        assert client.post("/api" + path, json=body).status_code == 409
        assert persisted(local) == before


def test_non_sqlite_and_remote_clients_cannot_enable_observed_records(local):
    _, repository, _ = local
    class CloudStyleRepository:
        def get(self, *args): return repository.get(*args)
        def create(self, *args): return repository.create(*args)
        def mutate(self, *args): return repository.mutate(*args)
    for app, peer in ((create_app(CloudStyleRepository()), ("testclient", 50000)),
                      (create_app(repository), ("198.51.100.4", 50000))):
        client = TestClient(app, client=peer)
        dashboard = client.get("/api/dashboard").json()
        client.headers["X-CSRF-Token"] = dashboard["csrf_token"]
        assert dashboard["features"]["local_observed_mode"] is False
        assert client.post("/api/workspace/live", json=SETTINGS).status_code == 403
        assert client.get("/api/dashboard").json()["mode"] == "SIMULATED_DEMO"


def test_explicit_demo_only_switch_disables_observed_mode_even_on_local_sqlite(local, monkeypatch):
    client, _, _ = local
    monkeypatch.setenv("JAL_DEMO_ONLY", "true")
    assert client.get("/api/dashboard").json()["features"]["local_observed_mode"] is False
    before = persisted(local)
    assert client.post("/api/workspace/live", json=SETTINGS).status_code == 403
    assert persisted(local) == before


def test_export_excludes_session_secrets_and_observed_records_survive_restart(local):
    observed(local)
    client, repository, _ = local
    dashboard = known_demand(client)
    exported = post(client, "/export", {})
    text = json.dumps(exported)
    assert exported["mode"] == "LOCAL_OBSERVED"
    assert exported["readings"] == persisted(local)["readings"]
    assert client.cookies.get("jal_session") not in text
    assert dashboard["csrf_token"] not in text
    assert "csrf_token" not in exported and "session_id" not in exported
    assert "unverified" in exported["note"].lower()
    restarted = TestClient(create_app(SQLiteRepository(repository.path)))
    restarted.cookies.update(client.cookies)
    restored = restarted.get("/api/dashboard").json()
    assert restored["site"]["id"] == dashboard["site"]["id"]
    assert restored["state"] == dashboard["state"]
    assert restored["mode"] == "LOCAL_OBSERVED"


def test_import_containing_unknown_interval_invalidates_earlier_recovery_batch(local):
    observed(local, {**SETTINGS, "lead_hours": 0, "buffer_hours": 0})
    client, _, clock = local
    rows = [reading(NOW - timedelta(hours=hour), 32000 + 960 * hour) for hour in range(12, 2, -1)]
    volume = rows[-1]["volume_l"]
    for number in range(1, 4):
        rows.append(reading(NOW - timedelta(hours=3 - number), volume - 2400 * number))
    danger = post(client, "/import", {"readings": rows})
    assert danger["incident"]["status"] == "OPEN"
    post(client, "/interventions", {"note": "Operator reports inspection"})
    volume = rows[-1]["volume_l"]
    for number in range(1, 3):
        clock["now"] = NOW + timedelta(minutes=30 * number)
        volume -= 480
        recovered = post(client, "/readings", reading(clock["now"], volume, f"independent-{number}"))
    assert recovered["incident"]["verification_count"] == 2
    clock["now"] = NOW + timedelta(hours=2)
    imported = post(client, "/import", {"readings": [
        reading(NOW + timedelta(minutes=90), volume + 100, "unknown-middle"),
        reading(clock["now"], volume + 100 - 480, "normal-batch-end"),
    ]})
    assert imported["analysis"]["status"] != "UNKNOWN"
    assert imported["incident"]["verification_count"] == 0
    clock["now"] += timedelta(minutes=30)
    subsequent = post(client, "/readings", reading(clock["now"], volume + 100 - 960, "one-independent-after"))
    assert subsequent["incident"]["verification_count"] == 1
    assert subsequent["incident"]["status"] != "RESOLVED"


@pytest.mark.parametrize("path", ["/workspace/live", "/site"])
@pytest.mark.parametrize("field, value", [
    ("measurement_error_l", "omitted"),
    ("measurement_error_l", None),
    ("measurement_error_l", ""),
    ("measurement_error_l", "100"),
    ("measurement_error_l", True),
    ("measurement_error_l", False),
    ("measurement_error_l", 0),
    ("measurement_error_l", -1),
    ("measurement_error_l", float("nan")),
    ("measurement_error_l", float("inf")),
    ("measurement_error_l", float("-inf")),
    ("measurement_error_l", 50000),
    ("measurement_error_basis", "omitted"),
    ("measurement_error_basis", None),
    ("measurement_error_basis", ""),
    ("measurement_error_basis", " \t\n "),
    ("measurement_error_basis", "\ufeff"),
    ("measurement_error_basis", " \ufeff\t\ufeff "),
    ("measurement_error_basis", True),
    ("measurement_error_basis", "x" * 301),
])
def test_sensor_error_declaration_is_required_and_rejected_settings_are_atomic(local, path, field, value):
    client, _, _ = local
    if path == "/site":
        observed(local)
        post(client, "/readings", reading(NOW, 32000, "retained-on-invalid-settings"))
    before = persisted(local)
    body = {**SETTINGS, field: value}
    if value == "omitted":
        del body[field]
    # HTTP JSON can contain nonstandard nonfinite values; reject them without
    # leaking an exception or changing the saved workspace.
    response = client.post("/api" + path, content=json.dumps(body), headers={"Content-Type": "application/json"})
    assert response.status_code == 422, response.text
    assert persisted(local) == before


def test_declared_sensor_error_basis_persists_and_is_disclosed_without_claiming_calibration(local):
    basis = "GENERATED TEST FIXTURE: simulator readings were bounded by 180 L; not a real sensor calibration."
    settings = {**SETTINGS, "measurement_error_l": 180, "measurement_error_basis": "  " + basis + "  "}
    observed(local, settings)
    client, repository, _ = local
    dashboard = known_demand(client)
    assert dashboard["site"]["measurement_error_l"] == 180
    assert dashboard["site"]["measurement_error_basis"] == basis
    assert dashboard["site"]["measurement_error_declared_at"] == NOW.isoformat()
    assert dashboard["analysis"]["status"] != "UNKNOWN"
    disclosure = " ".join(dashboard["analysis"]["facts"] + dashboard["analysis"]["forecast_assumptions"])
    assert basis in disclosure
    assert "180" in disclosure and "operator" in disclosure.lower()
    action = post(client, "/actions/propose", {"type": "REQUEST_SUPPLY"})
    assert basis in action["message"] and "180" in action["message"]
    assert "±" in action["message"] or "+/-" in action["message"]
    exported = post(client, "/export", {})
    assert exported["site"]["measurement_error_l"] == 180
    assert exported["site"]["measurement_error_basis"] == basis
    assert exported["site"]["measurement_error_declared_at"] == NOW.isoformat()
    restarted = TestClient(create_app(SQLiteRepository(repository.path)))
    restarted.cookies.update(client.cookies)
    restored = restarted.get("/api/dashboard").json()
    assert restored["site"]["measurement_error_l"] == 180
    assert restored["site"]["measurement_error_basis"] == basis
    assert restored["site"]["measurement_error_declared_at"] == NOW.isoformat()
    assert restored["analysis"]["projection"] == dashboard["analysis"]["projection"]


def test_legacy_undeclared_workspace_cannot_plan_or_approve_and_redeclaration_preserves_evidence(local):
    observed(local)
    client, repository, _ = local
    rows = [reading(NOW - timedelta(hours=hour), 32000 + 960 * hour) for hour in range(12, 2, -1)]
    volume = rows[-1]["volume_l"]
    rows.extend(reading(NOW - timedelta(hours=3 - number), volume - 2400 * number)
                for number in range(1, 4))
    danger = post(client, "/import", {"readings": rows})
    assert danger["incident"]["status"] == "OPEN"
    action = post(client, "/actions/propose", {"type": "REQUEST_INSPECTION"})
    session_id = client.cookies.get("jal_session")
    # Simulate a stored v0.2 workspace, which predates the basis requirement.
    # No migration should supply an invented operator declaration.
    repository.mutate(session_id, lambda context: context["site"].pop("measurement_error_basis"))
    before = persisted(local)
    dashboard = client.get("/api/dashboard").json()
    assert "measurement_error_basis" not in persisted(local)["site"]
    assert dashboard["state"]["data_state"] == "fresh"
    assert dashboard["state"]["volume_l"] == rows[-1]["volume_l"]
    assert dashboard["analysis"]["status"] == "UNKNOWN"
    assert dashboard["analysis"]["projection"] == []
    for field in ("reserve_breach_at", "conservative_breach_at", "latest_action_at", "action_margin_hours", "shortage_hours"):
        assert dashboard["analysis"].get(field) is None
    assert dashboard["incident"]["status"] == "UNKNOWN"
    assert dashboard["incident"]["lifecycle_status"] == "OPEN"
    for body in ({"type": "REQUEST_SUPPLY"}, {"type": "REQUEST_INSPECTION"}):
        assert client.post("/api/actions/propose", json=body).status_code == 409
        assert persisted(local) == before
    refused = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": True})
    assert refused.status_code == 409
    assert persisted(local) == before

    preview = post(client, "/simulate", {"delay_hours": 0, "added_supply_l": 50000, "demand_change_percent": -50})
    for analysis in (preview["analysis"], preview["before"]):
        assert analysis["status"] == "UNKNOWN"
        assert analysis["projection"] == []
        assert analysis["latest_action_at"] is None
    for question in ("deadline", "delay", "buffer"):
        answer = post(client, "/assistant", {"question": question})
        assert "unknown" in answer["answer"].lower()
        assert any("declar" in fact.lower() for fact in answer["facts"])
    assert persisted(local) == before

    declared = post(client, "/site", {**SETTINGS, "measurement_error_basis": "GENERATED TEST FIXTURE: redeclared +/−1 L bound, uncalibrated."})
    after = persisted(local)
    assert declared["analysis"]["status"] != "UNKNOWN"
    assert declared["analysis"]["projection"]
    assert declared["version"] > action["evidence_version"]
    assert after["readings"] == before["readings"]
    assert after["deliveries"] == before["deliveries"]
    assert after["actions"] == before["actions"]
    assert after["incident"] == before["incident"]
    assert declared["incident"]["id"] == danger["incident"]["id"]
    assert declared["incident"]["status"] == "OPEN"
    old_approval = client.post(f"/api/actions/{action['id']}/approve", json={"evidence_version": action["evidence_version"], "confirmed": True})
    assert old_approval.status_code == 409
    assert "Evidence changed" in old_approval.json()["detail"]
    fresh_action = post(client, "/actions/propose", {"type": "REQUEST_INSPECTION"})
    assert fresh_action["evidence_version"] == declared["version"]
    approved = post(client, f"/actions/{fresh_action['id']}/approve", {"evidence_version": fresh_action["evidence_version"], "confirmed": True})
    assert approved["actions"][-1]["status"] == "LOCAL_RECEIVED"
