"""Persistent isolated demo sessions with atomic updates."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

Context = dict
Mutation = Callable[[Context], None]


class SessionExpired(KeyError):
    pass


class SessionCapacityError(RuntimeError):
    pass


def serialized(context: Context) -> str:
    payload = json.dumps(context, separators=(",", ":"), allow_nan=False)
    if len(payload.encode("utf-8")) > 300000:
        raise ValueError("Workspace storage limit reached; export a backup before starting a new workspace")
    return payload


def expiry(context: Context) -> int:
    hours = 24 * 30 if context.get("mode") == "LOCAL_OBSERVED" else int(os.getenv("JAL_SESSION_TTL_HOURS", "24"))
    return int(time.time()) + hours * 3600


class SQLiteRepository:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, expires_at INTEGER NOT NULL)")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, session_id: str) -> Context | None:
        with self.connection() as db:
            row = db.execute("SELECT payload_json, expires_at FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if not row or row["expires_at"] <= int(time.time()):
            return None
        return json.loads(row["payload_json"])

    def create(self, session_id: str, context: Context) -> None:
        payload = serialized(context)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM sessions WHERE expires_at <= ?", (int(time.time()),))
            if db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] >= int(os.getenv("JAL_MAX_SESSIONS", "200")):
                raise SessionCapacityError("Local workspace capacity reached; wait for expired demo sessions to clear")
            db.execute("INSERT INTO sessions(session_id,payload_json,expires_at) VALUES (?,?,?)", (session_id, payload, expiry(context)))

    def mutate(self, session_id: str, operation: Mutation) -> Context:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload_json, expires_at FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            if not row or row["expires_at"] <= int(time.time()):
                raise SessionExpired("Session expired; reload the dashboard")
            context = json.loads(row["payload_json"])
            operation(context)
            db.execute("UPDATE sessions SET payload_json=?, version=version+1, expires_at=? WHERE session_id=?", (serialized(context), expiry(context), session_id))
            return context


class DynamoRepository:
    """Optimistic concurrency protects each isolated session in cloud mode."""
    def __init__(self, table_name: str):
        import boto3
        self.table = boto3.resource("dynamodb").Table(table_name)

    def get(self, session_id: str) -> Context | None:
        if session_id.startswith("quota#"):
            return None
        row = self.table.get_item(Key={"session_id": session_id}, ConsistentRead=True).get("Item")
        if not row or int(row["expires_at"]) <= int(time.time()):
            return None
        return json.loads(row["payload_json"])

    def create(self, session_id: str, context: Context) -> None:
        from botocore.exceptions import ClientError
        payload = serialized(context)
        hour = int(time.time()) // 3600
        # A conditional atomic counter bounds anonymous creation across Lambda
        # instances. Failed subsequent writes still consume quota conservatively.
        try:
            self.table.update_item(Key={"session_id": f"quota#{hour}"}, UpdateExpression="SET expires_at=:ttl ADD #count :one", ConditionExpression="attribute_not_exists(#count) OR #count < :limit", ExpressionAttributeNames={"#count": "count"}, ExpressionAttributeValues={":ttl": (hour + 48) * 3600, ":one": 1, ":limit": int(os.getenv("JAL_MAX_NEW_SESSIONS_PER_HOUR", "100"))})
        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise SessionCapacityError("Demo creation quota reached; try again next hour") from error
            raise
        self.table.put_item(Item={"session_id": session_id, "payload_json": payload, "version": 1, "expires_at": expiry(context)}, ConditionExpression="attribute_not_exists(session_id)")

    def mutate(self, session_id: str, operation: Mutation) -> Context:
        from botocore.exceptions import ClientError
        for _ in range(5):
            row = self.table.get_item(Key={"session_id": session_id}, ConsistentRead=True).get("Item")
            if not row or int(row["expires_at"]) <= int(time.time()):
                raise SessionExpired("Session expired; reload the dashboard")
            context = json.loads(row["payload_json"])
            operation(context)
            try:
                self.table.update_item(Key={"session_id": session_id}, UpdateExpression="SET payload_json=:payload, #v=:next, expires_at=:ttl", ConditionExpression="#v=:old AND expires_at > :now", ExpressionAttributeNames={"#v": "version"}, ExpressionAttributeValues={":payload": serialized(context), ":next": int(row["version"]) + 1, ":old": int(row["version"]), ":ttl": expiry(context), ":now": int(time.time())})
                return context
            except ClientError as error:
                if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    raise
        raise RuntimeError("Concurrent updates; retry the operation")


def make_repository():
    if os.getenv("JAL_STORAGE", "sqlite") == "dynamodb":
        table = os.getenv("JAL_TABLE_NAME")
        if not table:
            raise RuntimeError("JAL_TABLE_NAME is required for DynamoDB mode")
        return DynamoRepository(table)
    path = os.getenv("JAL_DB_PATH", str(Path(__file__).resolve().parent.parent / "runtime" / "jalrakshak.sqlite3"))
    return SQLiteRepository(path)
