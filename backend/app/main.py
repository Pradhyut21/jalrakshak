from __future__ import annotations

import json
import logging
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from . import operations
from .repository import make_repository

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
    volume_l: float = Field(ge=0, le=50000, allow_inf_nan=False)
    source: Literal["manual_demo"] = "manual_demo"
    simulated: Literal[True] = True
    advance_clock: StrictBool = False

    @field_validator("observed_at")
    @classmethod
    def aware_time(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone-aware observation required")
        return value


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
    app = FastAPI(title="JalRakshak", description="An honest, isolated simulated water-operations prototype.", version="0.1.0")
    app.state.repository = repository or make_repository()
    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        # Invalid numeric inputs such as NaN cannot themselves be JSON-encoded.
        # Return useful validation messages without echoing unsafe raw values.
        details = [{"loc": row["loc"], "msg": row["msg"], "type": row["type"]} for row in error.errors()]
        return JSONResponse(status_code=422, content={"detail": details})

    origins = [value.strip() for value in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000").split(",") if value.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-CSRF-Token"])

    def current_session(request: Request) -> str:
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
        return session_id

    def mutate(session_id: str, operation):
        try:
            result = app.state.repository.mutate(session_id, operation)
            return operations.dashboard(result, evaluation_data())
        except KeyError as error:
            raise HTTPException(404, str(error).strip("'")) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        except RuntimeError as error:
            raise HTTPException(409, str(error)) from error

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "isolated_simulated_demo", "storage": os.getenv("JAL_STORAGE", "sqlite"), "external_notifications": "disabled", "version": "0.1.0"}

    @app.get("/api/dashboard")
    def get_dashboard(request: Request, response: Response):
        session_id = request.cookies.get("jal_session", "")
        context = app.state.repository.get(session_id) if session_id else None
        if context is None:
            session_id = secrets.token_urlsafe(32)
            context = operations.seed()
            app.state.repository.create(session_id, context)
            secure = os.getenv("JAL_COOKIE_SECURE", "false").lower() == "true"
            response.set_cookie("jal_session", session_id, httponly=True, secure=secure, samesite="none" if secure else "lax", max_age=int(os.getenv("JAL_SESSION_TTL_HOURS", "24")) * 3600, path="/api")
        response.headers["Cache-Control"] = "no-store"
        return operations.dashboard(context, evaluation_data())

    @app.post("/api/demo/reset")
    def reset(session_id: str = Depends(current_session)):
        def replace(context):
            fresh = operations.seed(context["csrf_token"])
            context.clear()
            context.update(fresh)
        return mutate(session_id, replace)

    @app.post("/api/demo/scenario")
    def apply_scenario(body: ScenarioRequest, session_id: str = Depends(current_session)):
        return mutate(session_id, lambda context: operations.scenario(context, body.scenario, body.hours))

    @app.post("/api/readings")
    def post_reading(body: ReadingRequest, session_id: str = Depends(current_session)):
        reading = body.model_dump()
        advance = reading.pop("advance_clock")
        reading["observed_at"] = operations.iso(body.observed_at)
        def save(context):
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
        return mutate(session_id, save)

    @app.post("/api/simulate")
    def simulate(body: PreviewRequest, session_id: str = Depends(current_session)):
        context = app.state.repository.get(session_id)
        return operations.preview(context, body.delay_hours, body.added_supply_l, body.demand_change_percent)

    @app.post("/api/actions/propose")
    def propose(body: ProposalRequest, session_id: str = Depends(current_session)):
        result = mutate(session_id, lambda context: operations.propose(context, body.type))
        return result["actions"][-1]

    @app.post("/api/actions/{action_id}/approve")
    def approve(action_id: str, body: ApprovalRequest, session_id: str = Depends(current_session)):
        return mutate(session_id, lambda context: operations.approve(context, action_id, body.evidence_version, body.confirmed))

    @app.post("/api/interventions")
    def intervention(body: InterventionRequest, session_id: str = Depends(current_session)):
        return mutate(session_id, lambda context: operations.record_intervention(context, body.note))

    @app.post("/api/assistant")
    def assistant(body: AssistantRequest, session_id: str = Depends(current_session)):
        context = app.state.repository.get(session_id)
        analysis = operations.analysis_for(context)
        facts = analysis["facts"]
        if body.question == "deadline":
            answer = f"The planning deadline is {analysis.get('latest_action_at') or 'unknown'}. It uses the conservative reserve forecast minus {context['site']['lead_hours']} hours of supply lead time and {context['site']['buffer_hours']} hours of buffer. Unconfirmed supply is excluded."
        elif body.question == "delay":
            result = operations.preview(context, 6, 0, 0)
            shortage = result["analysis"]["shortage_hours"]
            answer = result["summary"] + (f" The central projected shortage is {shortage:.1f} hours within the modeled horizon." if shortage is not None else " Supply impact is unknown until sufficient fresh readings are available.")
        else:
            answer = f"Current planning margin: {analysis.get('action_margin_hours')} hours. Extra planned supply is conditional; it does not improve the conservative deadline until actual arrival evidence exists. Use the scenario delivery to observe the effect in simulated readings."
        return {"answer": answer, "facts": facts, "provider": "deterministic", "simulated": True}

    @app.get("/api/evaluation")
    def evaluation():
        return evaluation_data()

    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if (frontend_dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="interface")

    return app


app = create_app()
handler = Mangum(app, lifespan="off")
