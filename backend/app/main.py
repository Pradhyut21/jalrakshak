from __future__ import annotations

import json
import logging
import os
import secrets
import time
from collections import OrderedDict, deque
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from . import operations
from .repository import SQLiteRepository, SessionCapacityError, SessionExpired, make_repository

logger = logging.getLogger("jalrakshak")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScenarioRequest(StrictModel):
    scenario: Literal["excess_usage", "repair", "delivery"]
    hours: int = Field(default=2, ge=2, le=6)


class PreviewRequest(StrictModel):
    delay_hours: float = Field(default=6, ge=0, le=48, allow_inf_nan=False)
    added_supply_l: float = Field(default=0, ge=0, le=50000, allow_inf_nan=False)
    demand_change_percent: float = Field(default=0, ge=-50, le=100, allow_inf_nan=False)


class ReadingRequest(StrictModel):
    reading_id: str = Field(min_length=1, max_length=100)
    observed_at: datetime
    volume_l: float = Field(ge=0, le=10000000, allow_inf_nan=False)
    source: Literal["manual_demo", "manual_observed"] = "manual_demo"
    simulated: StrictBool = True
    advance_clock: StrictBool = False

    @field_validator("observed_at")
    @classmethod
    def aware_time(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone-aware observation required")
        return value


class SiteRequest(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    capacity_l: float = Field(gt=0, le=10000000, allow_inf_nan=False)
    reserve_l: float = Field(ge=0, allow_inf_nan=False)
    lead_hours: float = Field(ge=0, le=168, allow_inf_nan=False)
    buffer_hours: float = Field(ge=0, le=48, allow_inf_nan=False)
    measurement_error_l: float = Field(default=100, ge=0, allow_inf_nan=False)
    time_zone: str = Field(default="Asia/Kolkata", max_length=100)

    def settings(self):
        if self.reserve_l >= self.capacity_l or self.measurement_error_l >= self.capacity_l:
            raise HTTPException(422, "Reserve and declared reading error must be below tank capacity")
        if self.lead_hours + self.buffer_hours > 48:
            raise HTTPException(422, "Combined supply lead time and buffer cannot exceed the 48-hour forecast horizon")
        if self.time_zone not in {"Asia/Kolkata", "Asia/Calcutta", "UTC", "Etc/UTC"}:
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
            try:
                ZoneInfo(self.time_zone)
            except (ZoneInfoNotFoundError, ValueError) as error:
                raise HTTPException(422, "Unsupported timezone on this computer; use Asia/Kolkata or UTC") from error
        result = self.model_dump()
        result["name"] = self.name.strip()
        if not result["name"]:
            raise HTTPException(422, "Tank name cannot be blank")
        result["timezone"] = result.pop("time_zone")
        return result


class DeliveryRequest(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    amount_l: float = Field(gt=0, le=10000000, allow_inf_nan=False)
    arrived_at: datetime | None = None
    scheduled_at: datetime | None = None

    @field_validator("arrived_at", "scheduled_at")
    @classmethod
    def aware_time(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Timezone-aware delivery timestamp required")
        return value


class ImportRequest(StrictModel):
    readings: list[ReadingRequest] = Field(default_factory=list, max_length=1000)
    deliveries: list[DeliveryRequest] = Field(default_factory=list, max_length=100)


class ProposalRequest(StrictModel):
    type: Literal["REQUEST_SUPPLY", "REQUEST_INSPECTION"] = "REQUEST_SUPPLY"


class ApprovalRequest(StrictModel):
    evidence_version: int = Field(ge=1)
    confirmed: StrictBool


class InterventionRequest(StrictModel):
    type: Literal["REPAIR_RECORDED"] = "REPAIR_RECORDED"
    note: str = Field(default="Caretaker reports inspection", max_length=300)


class AssistantRequest(StrictModel):
    question: Literal["deadline", "delay", "buffer"]


def evaluation_data() -> dict:
    path = Path(__file__).resolve().parent / "data" / "evaluation.json"
    if not path.exists():
        path = Path(__file__).resolve().parent.parent.parent / "artifacts" / "evaluation.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"data_kind": "SIMULATED", "status": "pending", "summary": "Evaluation has not yet run"}


def create_app(repository=None) -> FastAPI:
    app = FastAPI(title="JalRakshak", description="Local tank records, reserve planning and evidence-based incident recovery.", version="0.2.0")
    app.state.repository = repository or make_repository()
    creations: OrderedDict[str, deque] = OrderedDict()
    creation_lock = Lock()

    def local_enabled(request):
        return isinstance(app.state.repository, SQLiteRepository) and os.getenv("JAL_DEMO_ONLY", "false").lower() != "true" and request.client is not None and request.client.host in {"127.0.0.1", "::1", "localhost", "testclient"}

    def ensure_local(request, context=None):
        if not local_enabled(request):
            raise HTTPException(403, "Observed records are available only on the local computer with SQLite storage")
        if context is not None and context["mode"] != "LOCAL_OBSERVED":
            raise ValueError("Start the local observed workspace before entering real records")

    def creation_budget(request):
        peer = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with creation_lock:
            for key in list(creations):
                if not creations[key] or creations[key][-1] <= now - 60:
                    del creations[key]
            attempts = creations.setdefault(peer, deque())
            while attempts and attempts[0] <= now - 60:
                attempts.popleft()
            if len(attempts) >= int(os.getenv("JAL_MAX_NEW_SESSIONS_PER_MINUTE", "6")):
                raise HTTPException(429, "Too many new workspaces; retry in one minute", headers={"Retry-After": "60"})
            if len(creations) > 512:
                creations.popitem(last=False)
            attempts.append(now)

    def dashboard(context, request):
        result = operations.dashboard(context, evaluation_data())
        result["features"] = {"local_observed_mode": local_enabled(request)}
        return result

    def cookie(response, session_id, context):
        secure = os.getenv("JAL_COOKIE_SECURE", "false").lower() == "true"
        hours = 720 if context["mode"] == "LOCAL_OBSERVED" else int(os.getenv("JAL_SESSION_TTL_HOURS", "24"))
        response.set_cookie("jal_session", session_id, httponly=True, secure=secure, samesite="none" if secure else "lax", max_age=hours * 3600, path="/api")
    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        # Invalid numeric inputs such as NaN cannot themselves be JSON-encoded.
        # Return useful validation messages without echoing unsafe raw values.
        details = [{"loc": row["loc"], "msg": row["msg"], "type": row["type"]} for row in error.errors()]
        return JSONResponse(status_code=422, content={"detail": details})

    origins = [value.strip() for value in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000").split(",") if value.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-CSRF-Token"])

    def current_session(request: Request) -> tuple[str, dict]:
        session_id = request.cookies.get("jal_session", "")
        context = app.state.repository.get(session_id) if session_id else None
        if context is None:
            raise HTTPException(401, "Session expired; reload the dashboard")
        origin = request.headers.get("origin")
        if origin and origin not in origins:
            raise HTTPException(403, "Origin is not allowed")
        token = request.headers.get("x-csrf-token", "")
        if not token or not secrets.compare_digest(token, context["csrf_token"]):
            raise HTTPException(403, "Valid session CSRF token required")
        operations.refresh_clock(context)
        operations.restore_incident_facts(context)
        return session_id, context

    def mutate(session, operation, request):
        session_id = session[0]
        def apply(context):
            operations.refresh_clock(context)
            operations.restore_incident_facts(context)
            operation(context)
        try:
            result = app.state.repository.mutate(session_id, apply)
            return dashboard(result, request)
        except SessionExpired as error:
            raise HTTPException(401, str(error).strip("'")) from error
        except KeyError as error:
            raise HTTPException(404, str(error).strip("'")) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        except RuntimeError as error:
            raise HTTPException(409, str(error)) from error

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "local_records_and_isolated_demo", "storage": os.getenv("JAL_STORAGE", "sqlite"), "external_notifications": "disabled", "version": "0.2.0"}

    @app.get("/api/dashboard")
    def get_dashboard(request: Request, response: Response):
        session_id = request.cookies.get("jal_session", "")
        context = app.state.repository.get(session_id) if session_id else None
        if context is None:
            creation_budget(request)
            session_id = secrets.token_urlsafe(32)
            context = operations.seed()
            try:
                app.state.repository.create(session_id, context)
            except SessionCapacityError as error:
                raise HTTPException(429, str(error), headers={"Retry-After": "60"}) from error
        cookie(response, session_id, context)
        response.headers["Cache-Control"] = "no-store"
        return dashboard(context, request)

    @app.post("/api/demo/reset")
    def reset(request: Request, session=Depends(current_session)):
        def replace(context):
            if context["mode"] != "SIMULATED_DEMO":
                raise ValueError("Demo reset is disabled for observed records; export your workspace before replacing it")
            fresh = operations.seed(context["csrf_token"])
            context.clear()
            context.update(fresh)
        return mutate(session, replace, request)

    @app.post("/api/demo/scenario")
    def apply_scenario(body: ScenarioRequest, request: Request, session=Depends(current_session)):
        return mutate(session, lambda context: operations.scenario(context, body.scenario, body.hours), request)

    @app.post("/api/readings")
    def post_reading(body: ReadingRequest, request: Request, session=Depends(current_session)):
        reading = body.model_dump()
        advance = reading.pop("advance_clock")
        reading["observed_at"] = operations.iso(body.observed_at)
        def save(context):
            if context["mode"] == "SIMULATED_DEMO":
                if body.source != "manual_demo" or body.simulated is not True or body.volume_l > 50000:
                    raise HTTPException(422, "Demo readings require manual_demo, simulated true and volume within the sample capacity")
            else:
                ensure_local(request, context)
                if body.source != "manual_observed" or body.simulated is not False or advance:
                    raise HTTPException(422, "Observed readings require manual_observed, simulated false and the server clock")
            if advance:
                from datetime import timedelta
                at = operations.parse(reading["observed_at"])
                now = operations.parse(context["clock"])
                if any(row["reading_id"] == reading["reading_id"] for row in context["readings"]):
                    operations.ingest(context, reading)
                    return
                if not now < at <= now + timedelta(hours=3):
                    raise ValueError("Demo clock advance must be later than now and at most three hours")
                context["clock"] = operations.iso(at)
                operations.event(context, "DEMO_CLOCK", "Demo clock advanced for an observation", "An explicit simulated manual entry advances this session only.")
            operations.ingest(context, reading)
        return mutate(session, save, request)

    @app.post("/api/simulate")
    def simulate(body: PreviewRequest, session=Depends(current_session)):
        context = session[1]
        return operations.preview(context, body.delay_hours, body.added_supply_l, body.demand_change_percent)

    @app.post("/api/workspace/live")
    def workspace(body: SiteRequest, request: Request, response: Response, session=Depends(current_session)):
        ensure_local(request)
        settings = body.settings()
        def replace(context):
            if context["mode"] == "LOCAL_OBSERVED":
                raise ValueError("An observed workspace already exists; update its settings instead")
            operations.observed_workspace(context, settings)
        result = mutate(session, replace, request)
        cookie(response, session[0], result)
        return result

    @app.post("/api/site")
    def site(body: SiteRequest, request: Request, session=Depends(current_session)):
        ensure_local(request, session[1])
        settings = body.settings()
        return mutate(session, lambda context: operations.update_site(context, settings), request)

    def delivery_record(body):
        if (body.arrived_at is None) == (body.scheduled_at is None):
            raise HTTPException(422, "Provide exactly one of arrived_at or scheduled_at")
        arrived = operations.iso(body.arrived_at) if body.arrived_at is not None else None
        scheduled = operations.iso(body.scheduled_at) if body.scheduled_at is not None else arrived
        return {"id": body.id, "amount_l": body.amount_l, "arrived_at": arrived, "scheduled_at": scheduled, "status": "ARRIVED" if arrived else "PLANNED"}

    @app.post("/api/deliveries")
    def delivery(body: DeliveryRequest, request: Request, session=Depends(current_session)):
        ensure_local(request, session[1])
        record = delivery_record(body)
        def save(context):
            if operations.ingest_delivery(context, record):
                operations.event(context, "DELIVERY", "Delivery record saved", "Arrival is operator-entered; a plan is conditional and never counted as actual inflow.")
        return mutate(session, save, request)

    @app.post("/api/import")
    def import_log(body: ImportRequest, request: Request, session=Depends(current_session)):
        ensure_local(request, session[1])
        readings = []
        for row in body.readings:
            if row.source != "manual_observed" or row.simulated is not False or row.advance_clock:
                raise HTTPException(422, "Imports require manual_observed readings, simulated false and server time")
            data = row.model_dump(exclude={"advance_clock"})
            data["observed_at"] = operations.iso(row.observed_at)
            readings.append(data)
        deliveries = [delivery_record(row) for row in body.deliveries]
        if any(row["status"] != "ARRIVED" for row in deliveries):
            raise HTTPException(422, "Log import accepts actual arrival records; enter future plans separately")
        return mutate(session, lambda context: operations.import_records(context, readings, deliveries), request)

    @app.post("/api/export")
    def export_records(session=Depends(current_session)):
        context = session[1]
        return {"schema_version": 1, "exported_at": context["clock"], "mode": context["mode"], "site": context["site"], "readings": context["readings"], "deliveries": context["deliveries"], "incident": context["incident"], "actions": context["actions"], "events": context["events"], "note": "Operator-entered records are unverified. This backup excludes session identifiers and CSRF secrets."}

    @app.post("/api/actions/propose")
    def propose(body: ProposalRequest, request: Request, session=Depends(current_session)):
        result = mutate(session, lambda context: operations.propose(context, body.type), request)
        return result["actions"][-1]

    @app.post("/api/actions/{action_id}/approve")
    def approve(action_id: str, body: ApprovalRequest, request: Request, session=Depends(current_session)):
        return mutate(session, lambda context: operations.approve(context, action_id, body.evidence_version, body.confirmed), request)

    @app.post("/api/interventions")
    def intervention(body: InterventionRequest, request: Request, session=Depends(current_session)):
        return mutate(session, lambda context: operations.record_intervention(context, body.note), request)

    @app.post("/api/assistant")
    def assistant(body: AssistantRequest, session=Depends(current_session)):
        context = session[1]
        analysis = operations.analysis_for(context)
        facts = analysis["facts"]
        if body.question == "deadline":
            answer = f"The planning deadline is {analysis.get('latest_action_at') or 'unknown'}. It uses the observed-demand planning envelope minus {context['site']['lead_hours']} hours of supply lead time and {context['site']['buffer_hours']} hours of buffer. Unconfirmed supply is excluded. It is assumption-dependent, not a guarantee."
        elif body.question == "delay":
            result = operations.preview(context, 6, 0, 0)
            shortage = result["analysis"]["shortage_hours"]
            answer = result["summary"] + (f" The central projected shortage is {shortage:.1f} hours within the modeled horizon." if shortage is not None else " Supply impact is unknown until sufficient fresh readings are available.")
        else:
            answer = f"Current planning margin: {analysis.get('action_margin_hours')} hours. Extra planned supply is conditional; it does not improve the planning envelope deadline until actual arrival records exist. Check recorded volumes, delivery lead time, buffer and measurement error before deciding."
        return {"answer": answer, "facts": facts, "provider": "deterministic", "simulated": context["mode"] == "SIMULATED_DEMO"}

    @app.get("/api/evaluation")
    def evaluation():
        return evaluation_data()

    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if (frontend_dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="interface")

    return app


app = create_app()
handler = Mangum(app, lifespan="off")
