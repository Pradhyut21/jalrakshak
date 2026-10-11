"""Observed-error disclosures at the HTTP boundary; fixtures are synthetic."""
from copy import deepcopy
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app import operations
from backend.app.domain import analyze
from backend.app.main import create_app
from backend.app.repository import SQLiteRepository
from backend.tests.test_observed_workspace import (
    NOW, SETTINGS, known_demand, local, observed, persisted, post,
)


@pytest.mark.parametrize("path", ["/workspace/live", "/site"])
@pytest.mark.parametrize("capacity, error, warns", [
    (50000, 249, True), (50000, 250, False), (50000, 251, False),
    (10000, 49, True), (10000, 50, False), (10000, 51, False),
])
def test_review_threshold_is_strict_and_scales_with_declared_capacity(local, path, capacity, error, warns):
    client, _, _ = local
    if path == "/site":
        observed(local)
    result = post(client, path, {**SETTINGS, "capacity_l": capacity,
                                "measurement_error_l": error})
    assert result["site"]["measurement_error_l"] == error
    warning = result["analysis"]["measurement_error_warning"]
    if warns:
        assert warning["code"] == "LOW_DECLARED_ERROR"
        assert warning["declared_error_l"] == error
        assert warning["capacity_percent"] == pytest.approx(error / capacity * 100)
        assert warning["review_threshold_percent"] == 0.5
        assert warning["review_threshold_l"] == capacity * 0.005
    else:
        assert warning is None


def test_one_litre_and_one_letter_basis_remain_accepted_but_explicitly_warn(local):
    observed(local, {**SETTINGS, "measurement_error_l": 1, "measurement_error_basis": "x"})
    client, _, _ = local
    result = known_demand(client)
    assert result["analysis"]["status"] != "UNKNOWN"
    assert result["analysis"]["projection"]
    assert result["analysis"]["latest_action_at"] is not None
    assert result["site"]["measurement_error_l"] == 1
    assert result["site"]["measurement_error_basis"] == "x"
    warning = result["analysis"]["measurement_error_warning"]
    text = warning["message"].lower()
    assert "0.5%" in text and "heuristic" in text
    assert "calibration" in text and "late" in text
    assert "minimum" in text or "requirement" in text
    assert warning["message"] in result["analysis"]["facts"]


def test_warning_disclosure_does_not_change_domain_analysis_or_forecast(local):
    observed(local)
    client, _, _ = local
    result = known_demand(client)["analysis"]
    context = persisted(local)
    expected = analyze(operations.analysis_site(context), context["readings"],
                       context["deliveries"], operations.parse(context["clock"]))
    actual = deepcopy(result)
    warning = actual.pop("measurement_error_warning")
    # Only the disclosure may be added to the domain's original result.
    for field in ("facts", "forecast_assumptions"):
        actual[field] = [line for line in actual[field] if line != warning["message"]]
    assert actual == expected
    assert persisted(local) == context


@pytest.mark.parametrize("stale", [False, True])
def test_warning_survives_empty_or_stale_unknown_without_forecast(local, stale):
    observed(local)
    client, _, clock = local
    if stale:
        known_demand(client)
        clock["now"] = NOW + timedelta(minutes=91)
    result = client.get("/api/dashboard").json()
    assert result["analysis"]["status"] == "UNKNOWN"
    assert result["analysis"]["projection"] == []
    assert result["analysis"]["latest_action_at"] is None
    assert result["analysis"]["conservative_breach_at"] is None
    warning = result["analysis"]["measurement_error_warning"]
    assert warning["code"] == "LOW_DECLARED_ERROR"
    assert warning["message"] in result["analysis"]["facts"]
    response = post(client, "/assistant", {"question": "deadline"})
    assert "unknown" in response["answer"].lower()
    assert warning["message"] in response["facts"]
    assert warning["message"] in response["answer"]
    assert client.post("/api/actions/propose", json={"type": "REQUEST_SUPPLY"}).status_code == 409


def test_preview_assistant_and_local_notice_preserve_warning_without_new_approval_gate(local):
    observed(local)
    client, _, _ = local
    dashboard = known_demand(client)
    warning = dashboard["analysis"]["measurement_error_warning"]
    preview = post(client, "/simulate", {"delay_hours": 6, "added_supply_l": 1000,
                                         "demand_change_percent": -25})
    for analysis in (preview["before"], preview["analysis"]):
        assert analysis["measurement_error_warning"] == warning
        assert warning["message"] in analysis["facts"]
    for question in ("deadline", "delay", "buffer"):
        reply = post(client, "/assistant", {"question": question})
        assert warning["message"] in reply["facts"]
        assert warning["message"] in reply["answer"]
    action = post(client, "/actions/propose", {"type": "REQUEST_SUPPLY"})
    assert warning["message"] in action["message"]
    approved = post(client, f"/actions/{action['id']}/approve",
                    {"evidence_version": action["evidence_version"], "confirmed": True})
    assert approved["actions"][-1]["status"] == "LOCAL_RECEIVED"
    assert warning["message"] in approved["actions"][-1]["message"]
    assert approved["analysis"]["measurement_error_warning"] == warning


def test_demo_and_legacy_missing_declaration_have_no_plausibility_warning(local):
    client, repository, _ = local
    assert client.get("/api/dashboard").json()["analysis"]["measurement_error_warning"] is None
    observed(local)
    known_demand(client)
    session_id = client.cookies.get("jal_session")
    repository.mutate(session_id, lambda context: context["site"].pop("measurement_error_basis"))
    result = client.get("/api/dashboard").json()
    assert result["analysis"]["measurement_error_warning"] is None
    assert result["analysis"]["status"] == "UNKNOWN"
    assert result["analysis"]["projection"] == []
    assert result["analysis"]["recommendation"]["type"] == "CONFIGURE_SITE"


def test_above_threshold_is_still_uncalibrated_and_not_a_safety_certification(local):
    observed(local, {**SETTINGS, "measurement_error_l": 1000})
    client, _, _ = local
    result = known_demand(client)["analysis"]
    assert result["measurement_error_warning"] is None
    disclosure = " ".join(result["facts"] + result["forecast_assumptions"]).lower()
    assert "declaration is not calibration" in disclosure
    assert "understated bound can produce late warnings" in disclosure
    assert "guarantee" in result["forecast_description"].lower()


def test_export_and_restart_keep_operator_bound_without_autocorrection(local):
    basis = "x"
    observed(local, {**SETTINGS, "measurement_error_l": 1, "measurement_error_basis": basis})
    client, repository, _ = local
    dashboard = known_demand(client)
    exported = post(client, "/export", {})
    assert exported["site"]["measurement_error_l"] == 1
    assert exported["site"]["measurement_error_basis"] == basis
    assert exported["readings"] == persisted(local)["readings"]
    restarted = TestClient(create_app(SQLiteRepository(repository.path)))
    restarted.cookies.update(client.cookies)
    restored = restarted.get("/api/dashboard").json()
    assert restored["site"]["measurement_error_l"] == 1
    assert restored["site"]["measurement_error_basis"] == basis
    assert restored["analysis"]["measurement_error_warning"] == dashboard["analysis"]["measurement_error_warning"]
    assert restored["analysis"]["projection"] == dashboard["analysis"]["projection"]
