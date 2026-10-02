"""Expiry, resource bounds and atomic rollback; Dynamo tests use an offline fake."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from backend.app import main, repository as storage
from backend.app.operations import seed
from backend.app.repository import DynamoRepository, SessionCapacityError, SessionExpired, SQLiteRepository


@pytest.fixture
def repository(tmp_path, monkeypatch):
    monkeypatch.setenv("JAL_MAX_SESSIONS", "200")
    monkeypatch.setenv("JAL_SESSION_TTL_HOURS", "24")
    monkeypatch.setenv("JAL_MAX_NEW_SESSIONS_PER_MINUTE", "6")
    monkeypatch.setenv("JAL_COOKIE_SECURE", "false")
    return SQLiteRepository(str(tmp_path / "limits.sqlite3"))


def stored_row(repository, identity):
    with repository.connection() as db:
        row = db.execute("SELECT * FROM sessions WHERE session_id=?", (identity,)).fetchone()
        return dict(row) if row else None


def started(repository):
    client = TestClient(main.create_app(repository))
    dashboard = client.get("/api/dashboard").json()
    client.headers["X-CSRF-Token"] = dashboard["csrf_token"]
    return client, dashboard


def test_sqlite_creation_cap_is_atomic_under_simultaneous_new_sessions(repository, monkeypatch):
    monkeypatch.setenv("JAL_MAX_SESSIONS", "3")
    barrier = Barrier(8)
    def create(number):
        barrier.wait(timeout=10)
        try:
            repository.create(f"parallel-{number}", seed())
            return "created"
        except SessionCapacityError:
            return "capacity"
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(create, range(8)))
    assert outcomes.count("created") == 3
    assert outcomes.count("capacity") == 5
    with repository.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 3


def test_expired_sessions_clear_before_capacity_check_including_exact_boundary(repository, monkeypatch):
    monkeypatch.setenv("JAL_MAX_SESSIONS", "2")
    clock = {"time": 2000000000}
    monkeypatch.setattr(storage, "time", SimpleNamespace(time=lambda: clock["time"]))
    repository.create("expired", seed())
    repository.create("live", seed())
    with repository.connection() as db:
        db.execute("UPDATE sessions SET expires_at=? WHERE session_id='expired'", (clock["time"],))
    assert repository.get("expired") is None
    repository.create("replacement", seed())
    assert stored_row(repository, "expired") is None
    assert repository.get("live") is not None
    assert repository.get("replacement") is not None
    with pytest.raises(SessionCapacityError):
        repository.create("too-many", seed())


def test_observed_ttl_is_30_days_after_write_and_reads_do_not_extend_it(repository, monkeypatch):
    clock = {"time": 2000000000}
    monkeypatch.setattr(storage, "time", SimpleNamespace(time=lambda: clock["time"]))
    observed = {"mode": "LOCAL_OBSERVED", "marker": "original"}
    repository.create("observed", observed)
    repository.create("demo", seed())
    assert stored_row(repository, "observed")["expires_at"] == clock["time"] + 30 * 86400
    assert stored_row(repository, "demo")["expires_at"] == clock["time"] + 86400
    original_expiry = stored_row(repository, "observed")["expires_at"]
    clock["time"] += 10 * 86400
    assert repository.get("observed") == observed
    assert stored_row(repository, "observed")["expires_at"] == original_expiry
    repository.mutate("observed", lambda context: context.update(marker="new write"))
    assert stored_row(repository, "observed")["expires_at"] == clock["time"] + 30 * 86400
    clock["time"] += 30 * 86400
    assert repository.get("observed") is None
    with pytest.raises(SessionExpired):
        repository.mutate("observed", lambda context: context.update(marker="resurrected"))


@pytest.mark.parametrize("path, body", [("/simulate", {}), ("/assistant", {"question": "deadline"}),
                                       ("/export", {}), ("/demo/reset", {}), ("/actions/propose", {})])
def test_expired_session_returns_401_for_reads_and_mutations(repository, path, body):
    client, _ = started(repository)
    session = client.cookies.get("jal_session")
    with repository.connection() as db:
        db.execute("UPDATE sessions SET expires_at=0 WHERE session_id=?", (session,))
    response = client.post("/api" + path, json=body)
    assert response.status_code == 401
    assert "Session expired" in response.json()["detail"]
    assert stored_row(repository, session)["version"] == 1


def test_expiry_between_authentication_and_mutation_is_401_not_404_or_500(repository, monkeypatch):
    client, _ = started(repository)
    session = client.cookies.get("jal_session")
    mutate = repository.mutate
    def expire_before_write(identity, operation):
        with repository.connection() as db:
            db.execute("UPDATE sessions SET expires_at=0 WHERE session_id=?", (identity,))
        return mutate(identity, operation)
    monkeypatch.setattr(repository, "mutate", expire_before_write)
    response = client.post("/api/demo/reset", json={})
    assert response.status_code == 401
    assert stored_row(repository, session)["version"] == 1


def test_read_endpoint_uses_authenticated_snapshot_if_expiry_occurs_after_read(repository, monkeypatch):
    client, _ = started(repository)
    original_get = repository.get
    calls = []
    def expire_after_read(identity):
        context = original_get(identity)
        calls.append(identity)
        with repository.connection() as db:
            db.execute("UPDATE sessions SET expires_at=0 WHERE session_id=?", (identity,))
        return context
    monkeypatch.setattr(repository, "get", expire_after_read)
    response = client.post("/api/assistant", json={"question": "deadline"})
    assert response.status_code == 200
    assert response.json()["provider"] == "deterministic"
    assert len(calls) == 1  # No unsafe second fetch that becomes None mid-request.


def test_expired_dashboard_creates_new_isolated_session_and_rejects_old_csrf(repository):
    client, initial = started(repository)
    expired_session = client.cookies.get("jal_session")
    with repository.connection() as db:
        db.execute("UPDATE sessions SET expires_at=0 WHERE session_id=?", (expired_session,))
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    fresh = response.json()
    assert client.cookies.get("jal_session") != expired_session
    assert fresh["csrf_token"] != initial["csrf_token"]
    assert stored_row(repository, expired_session) is None
    assert client.post("/api/demo/reset", json={}).status_code == 403


def test_new_session_request_rate_is_bounded_but_existing_session_stays_available(repository, monkeypatch):
    monkeypatch.setenv("JAL_MAX_NEW_SESSIONS_PER_MINUTE", "2")
    clock = {"monotonic": 1000.0}
    monkeypatch.setattr(main, "time", SimpleNamespace(monotonic=lambda: clock["monotonic"]))
    app = main.create_app(repository)
    first, second, third = (TestClient(app) for _ in range(3))
    assert first.get("/api/dashboard").status_code == 200
    assert second.get("/api/dashboard").status_code == 200
    refused = third.get("/api/dashboard")
    assert refused.status_code == 429
    assert refused.headers["Retry-After"] == "60"
    assert first.get("/api/dashboard").status_code == 200
    clock["monotonic"] += 60
    assert third.get("/api/dashboard").status_code == 200


def test_http_session_capacity_returns_retryable_429_without_issuing_an_unstored_cookie(repository, monkeypatch):
    monkeypatch.setenv("JAL_MAX_SESSIONS", "1")
    app = main.create_app(repository)
    first, second = TestClient(app), TestClient(app)
    assert first.get("/api/dashboard").status_code == 200
    refused = second.get("/api/dashboard")
    assert refused.status_code == 429
    assert "capacity" in refused.json()["detail"].lower()
    assert "jal_session" not in second.cookies
    assert first.get("/api/dashboard").status_code == 200


def test_oversized_utf8_payload_rolls_back_all_changes_version_and_ttl(repository, monkeypatch):
    clock = {"time": 2000000000}
    monkeypatch.setattr(storage, "time", SimpleNamespace(time=lambda: clock["time"]))
    repository.create("bounded", {"mode": "SIMULATED_DEMO", "marker": "original"})
    before = stored_row(repository, "bounded")
    clock["time"] += 100
    def oversized(context):
        context.update(marker="must not persist", blob="🙂" * 80000)
    with pytest.raises(ValueError, match="storage limit"):
        repository.mutate("bounded", oversized)
    assert stored_row(repository, "bounded") == before
    assert repository.get("bounded")["marker"] == "original"
    with pytest.raises(ValueError, match="storage limit"):
        repository.create("oversized-new", {"mode": "SIMULATED_DEMO", "blob": "x" * 300001})
    assert stored_row(repository, "oversized-new") is None


def test_nonfinite_payload_is_rejected_before_any_partial_write(repository):
    repository.create("finite", {"mode": "SIMULATED_DEMO", "marker": "original"})
    before = stored_row(repository, "finite")
    with pytest.raises(ValueError):
        repository.mutate("finite", lambda context: context.update(marker="changed", quantity=float("nan")))
    assert stored_row(repository, "finite") == before


class OfflineQuotaTable:
    """Only models the conditional counter protocol; this is not AWS validation."""
    def __init__(self):
        self.rows = {}
        self.calls = []
        self.lock = Lock()
    def update_item(self, **request):
        with self.lock:
            self.calls.append(request)
            key = request["Key"]["session_id"]
            assert key.startswith("quota#")
            assert request["ConditionExpression"] == "attribute_not_exists(#count) OR #count < :limit"
            values = request["ExpressionAttributeValues"]
            current = self.rows.get(key, {"count": 0})
            if current["count"] >= values[":limit"]:
                raise ClientError({"Error": {"Code": "ConditionalCheckFailedException", "Message": "quota full"}}, "UpdateItem")
            self.rows[key] = {"count": current["count"] + values[":one"], "expires_at": values[":ttl"]}
    def put_item(self, **request):
        with self.lock:
            key = request["Item"]["session_id"]
            assert request["ConditionExpression"] == "attribute_not_exists(session_id)"
            self.rows[key] = request["Item"]


def test_dynamo_creation_counter_bounds_shared_hour_and_rolls_into_next_hour_offline(monkeypatch):
    monkeypatch.setenv("JAL_MAX_NEW_SESSIONS_PER_HOUR", "2")
    clock = {"time": 2000000000}
    monkeypatch.setattr(storage, "time", SimpleNamespace(time=lambda: clock["time"]))
    table = OfflineQuotaTable()
    repository = DynamoRepository.__new__(DynamoRepository)
    repository.table = table
    repository.create("first", seed())
    repository.create("second", seed())
    with pytest.raises(SessionCapacityError, match="quota"):
        repository.create("third", seed())
    hour = clock["time"] // 3600
    assert table.rows[f"quota#{hour}"]["count"] == 2
    assert "third" not in table.rows
    assert table.rows[f"quota#{hour}"]["expires_at"] == (hour + 48) * 3600
    assert repository.get(f"quota#{hour}") is None  # Quota records cannot become session payloads.
    clock["time"] += 3600
    repository.create("next-hour", seed())
    assert table.rows[f"quota#{hour + 1}"]["count"] == 1


def test_dynamo_oversized_creation_does_not_consume_creation_counter_offline():
    table = OfflineQuotaTable()
    repository = DynamoRepository.__new__(DynamoRepository)
    repository.table = table
    with pytest.raises(ValueError, match="storage limit"):
        repository.create("too-large", {"mode": "SIMULATED_DEMO", "blob": "x" * 300001})
    assert table.rows == {} and table.calls == []
