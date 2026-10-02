"""Seed, ingest, propose, approve, and verify using server-owned evidence."""
from __future__ import annotations

import copy
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .domain import analyze, analyze_preview


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def event(context: dict, kind: str, title: str, detail: str) -> None:
    context["events"].append({"id": str(uuid4()), "at": context["clock"], "kind": kind, "title": title, "detail": detail})
    context["events"] = context["events"][-100:]


def seed(csrf_token: str | None = None) -> dict:
    now = datetime(2026, 10, 1, 4, 30, tzinfo=timezone.utc)
    context = {
        "site": {"id": "hostel-1", "name": "Aravali Student Hostel", "location": "New Delhi · Sample campus", "capacity_l": 50000, "reserve_l": 5000, "lead_hours": 14, "buffer_hours": 3, "freshness_minutes": 90},
        "clock": iso(now), "mode": "SIMULATED_DEMO", "version": 1,
        "csrf_token": csrf_token or secrets.token_urlsafe(32), "readings": [], "deliveries": [],
        "incident": None, "actions": [], "events": [], "excess_active": False,
    }
    start = now - timedelta(hours=72)
    volume = 29120.0
    for hour in range(73):
        at = start + timedelta(hours=hour)
        if hour:
            volume -= 960
            if hour % 24 == 0:
                volume += 24000
                context["deliveries"].append({"id": f"historical-{hour}", "scheduled_at": iso(at), "arrived_at": iso(at), "amount_l": 24000, "status": "ARRIVED"})
        context["readings"].append({"reading_id": f"seed-{hour}", "observed_at": iso(at), "volume_l": volume, "source": "synthetic_demo", "simulated": True})
    context["deliveries"].append({"id": "planned-next", "scheduled_at": iso(now + timedelta(hours=18)), "arrived_at": None, "amount_l": 18000, "status": "PLANNED"})
    event(context, "SYSTEM", "A fresh start", "72 hours of simulated readings loaded. No real campus sensors or external messages.")
    return context


def analysis_for(context: dict) -> dict:
    return analyze(context["site"], context["readings"], context["deliveries"], parse(context["clock"]))


def reconcile(context: dict, reading_id: str | None = None) -> None:
    analysis = analysis_for(context)
    incident = context["incident"]
    if analysis["anomaly"]["active"] and (not incident or incident["status"] == "RESOLVED"):
        context["incident"] = {"id": str(uuid4()), "status": "OPEN", "opened_at": context["clock"], "intervention_at": None, "verified_at": None, "verification_count": 0, "verification_reading_ids": [], "reason": "Sustained abnormal site-level depletion. This is not confirmation of a physical leak."}
        event(context, "ANOMALY", "Abnormal depletion detected", analysis["anomaly"]["reason"])
        incident = context["incident"]
    if not incident or incident["status"] == "RESOLVED":
        return
    if analysis["status"] == "UNKNOWN":
        incident["status"] = "UNKNOWN"
        incident["verification_reading_ids"] = []
        incident["verification_count"] = 0
        return
    if not incident["intervention_at"]:
        return
    incident["status"] = "VERIFYING"
    newest = max(context["readings"], key=lambda row: parse(row["observed_at"]))
    eligible = reading_id and parse(newest["observed_at"]) > parse(incident["intervention_at"]) and reading_id == newest["reading_id"]
    last_rate = analysis["history"][-1]["rate_lph"] if analysis["history"] else None
    baseline = analysis["baseline_rate_lph"]
    normal_interval = last_rate is not None and baseline is not None and last_rate <= baseline * 1.25
    margin = analysis.get("action_margin_hours")
    adequate_margin = (margin is not None and margin >= 3) or (margin is None and analysis["conservative_breach_at"] is None and analysis["status"] == "SAFE")
    recovered = not analysis["anomaly"]["active"] and normal_interval and adequate_margin
    if eligible and reading_id not in incident["verification_reading_ids"]:
        if recovered:
            incident["verification_reading_ids"].append(reading_id)
        else:
            incident["verification_reading_ids"] = []
        incident["verification_count"] = len(incident["verification_reading_ids"])
    if incident["verification_count"] >= 3:
        incident["status"] = "RESOLVED"
        incident["verified_at"] = context["clock"]
        incident["reason"] = "Three fresh simulated post-intervention readings show normal depletion and at least three hours of planning margin. Physical repair is not verified."
        event(context, "VERIFIED", "Recovery verified in the scenario", incident["reason"])


def ingest(context: dict, reading: dict) -> bool:
    if reading["volume_l"] > context["site"]["capacity_l"] or reading["volume_l"] < 0:
        raise ValueError("Reading must be between zero and tank capacity")
    if parse(reading["observed_at"]) > parse(context["clock"]):
        raise ValueError("The observation cannot be later than the current simulated clock")
    for old in context["readings"]:
        if old["reading_id"] == reading["reading_id"]:
            if old != reading:
                raise ValueError("Reading ID already exists with a different payload")
            return False
        if parse(old["observed_at"]) == parse(reading["observed_at"]) and old["volume_l"] != reading["volume_l"]:
            raise ValueError("A conflicting observation already exists at this timestamp")
    incident = context["incident"]
    newest_at = max(parse(row["observed_at"]) for row in context["readings"])
    if incident and incident["intervention_at"] and parse(reading["observed_at"]) < newest_at:
        # Late data can change already-counted intervals or the historical baseline.
        # Require a new batch rather than retaining a verdict based on old evidence.
        incident.update(status="VERIFYING", verification_count=0, verification_reading_ids=[], verified_at=None)
        incident["reason"] = "Historical evidence changed; recovery needs a new batch of fresh observations."
        event(context, "EVIDENCE_REVISION", "Recovery evidence revised", incident["reason"])
    context["readings"].append(reading)
    context["readings"].sort(key=lambda row: parse(row["observed_at"]))
    context["readings"] = context["readings"][-500:]
    context["version"] += 1
    reconcile(context, reading["reading_id"])
    return True


def record_intervention(context: dict, note: str) -> None:
    if context["incident"] and context["incident"]["status"] != "RESOLVED":
        incident = context["incident"]
        incident.update(status="VERIFYING", intervention_at=context["clock"], verification_count=0, verification_reading_ids=[])
    context["version"] += 1
    event(context, "INTERVENTION", "Intervention recorded", note + " Awaiting fresh readings; this does not prove a repair.")


def scenario(context: dict, name: str, hours: int) -> None:
    if name == "excess_usage":
        context["excess_active"] = True
        event(context, "SCENARIO", "Sustained excess-use scenario", "New simulated observations will reflect 2,400 L/h site-level depletion.")
    elif name == "repair":
        context["excess_active"] = False
        record_intervention(context, "A simulated repair is reported")
    elif name == "delivery":
        record_intervention(context, "An extra simulated delivery is recorded")
    else:
        raise ValueError("Unknown scenario")
    pending_delivery = name == "delivery"
    for step in range(hours * 2):
        previous = max(context["readings"], key=lambda row: parse(row["observed_at"]))
        at = parse(context["clock"]) + timedelta(minutes=30)
        rate = 2400 if context["excess_active"] else 960
        volume = float(previous["volume_l"]) - rate / 2
        if pending_delivery:
            volume += 18000
            context["deliveries"].append({"id": str(uuid4()), "scheduled_at": iso(at), "arrived_at": iso(at), "amount_l": 18000, "status": "ARRIVED"})
            event(context, "DELIVERY", "18,000 L simulated delivery", "Arrival entered in the inflow ledger; the next observation becomes the new volume anchor.")
            pending_delivery = False
        volume = max(0.0, min(context["site"]["capacity_l"], volume))
        context["clock"] = iso(at)
        ingest(context, {"reading_id": str(uuid4()), "observed_at": iso(at), "volume_l": volume, "source": "synthetic_demo", "simulated": True})


def propose(context: dict, action_type: str) -> dict:
    if len(context["actions"]) >= 20:
        raise ValueError("Demo action limit reached; reset this isolated session")
    analysis = analysis_for(context)
    if analysis["status"] == "UNKNOWN":
        raise ValueError("Insufficient fresh evidence to propose an operational request")
    if action_type not in {"REQUEST_SUPPLY", "REQUEST_INSPECTION"}:
        raise ValueError("Unsupported request type")
    deadline = analysis.get("latest_action_at")
    message = f"SIMULATED DEMO — {context['site']['name']}. {analysis['recommendation']['body']} Planning deadline: {deadline or 'not established'}. This request does not book a tanker or confirm a repair."
    action = {"id": str(uuid4()), "type": action_type, "status": "PROPOSED", "created_at": context["clock"], "approved_at": None, "published_at": None, "receipt_at": None, "evidence_version": context["version"], "message": message, "destination": "This session's local notice inbox", "expires_at": iso(parse(context["clock"]) + timedelta(hours=1))}
    context["actions"].append(action)
    event(context, "PROPOSAL", "Notice ready for review", "Explicit approval is required. Destination: this session's local inbox.")
    return action


def approve(context: dict, action_id: str, evidence_version: int, confirmed: bool) -> None:
    action = next((row for row in context["actions"] if row["id"] == action_id), None)
    if not action:
        raise KeyError("Action not found in this session")
    if not confirmed:
        raise ValueError("Explicit confirmation is required")
    if action["status"] == "LOCAL_RECEIVED":
        return
    if action["evidence_version"] != evidence_version or context["version"] != evidence_version:
        raise ValueError("Evidence changed; review a new proposal")
    if parse(context["clock"]) > parse(action["expires_at"]):
        raise ValueError("Proposal expired; create a new proposal")
    if analysis_for(context)["status"] == "UNKNOWN":
        raise ValueError("Fresh usable evidence is required before approval")
    action.update(status="LOCAL_RECEIVED", approved_at=context["clock"], published_at=None, receipt_at=context["clock"])
    if context["incident"] and context["incident"]["status"] == "OPEN":
        context["incident"]["status"] = "ACTION_REQUESTED"
    event(context, "NOTICE", "Approved notice received locally", "Persisted in your isolated inbox. No external message, tanker booking or physical repair was performed.")


def preview(context: dict, delay_hours: float, added_supply_l: float, demand_change_percent: float) -> dict:
    before = analysis_for(context)
    changed = copy.deepcopy(context)
    now = parse(context["clock"])
    for delivery in changed["deliveries"]:
        if delivery["status"] == "PLANNED":
            delivery["scheduled_at"] = iso(parse(delivery["scheduled_at"]) + timedelta(hours=delay_hours))
    if added_supply_l:
        changed["deliveries"].append({"id": "hypothetical-supply", "scheduled_at": iso(now + timedelta(hours=changed["site"]["lead_hours"])), "arrived_at": None, "amount_l": added_supply_l, "status": "PLANNED"})
    result = analyze_preview(changed["site"], changed["readings"], changed["deliveries"], now, demand_change_percent)
    summary = f"Preview only: supply delayed by {delay_hours:g} h, extra planned supply {added_supply_l:,.0f} L, demand change {demand_change_percent:+g}%. Unconfirmed supply is excluded from the conservative action deadline."
    return {"analysis": result, "before": before, "summary": summary, "simulated": True}


def dashboard(context: dict, evaluation: dict | None = None) -> dict:
    newest = max(context["readings"], key=lambda row: parse(row["observed_at"]))
    analysis = analysis_for(context)
    state = {"volume_l": newest["volume_l"], "percentage": round(newest["volume_l"] / context["site"]["capacity_l"] * 100, 1), "observed_at": newest["observed_at"], "source": newest["source"], "simulated": newest["simulated"], "data_state": "stale" if parse(context["clock"]) - parse(newest["observed_at"]) > timedelta(minutes=context["site"]["freshness_minutes"]) else "fresh"}
    return {"site": context["site"], "clock": context["clock"], "mode": context["mode"], "version": context["version"], "csrf_token": context["csrf_token"], "state": state, "analysis": analysis, "incident": context["incident"], "actions": context["actions"], "events": context["events"], "evaluation": evaluation or {"data_kind": "SIMULATED", "status": "pending", "summary": "Evaluation has not yet run"}}
