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
        ttl = int(time.time()) + int(os.getenv("JAL_SESSION_TTL_HOURS", "24")) * 3600
        with self.connection() as db:
            db.execute("DELETE FROM sessions WHERE expires_at < ?", (int(time.time()),))
            db.execute("INSERT INTO sessions(session_id,payload_json,expires_at) VALUES (?,?,?)", (session_id, json.dumps(context), ttl))

    def mutate(self, session_id: str, operation: Mutation) -> Context:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload_json, expires_at FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            if not row or row["expires_at"] <= int(time.time()):
                raise KeyError("Session expired; reload the dashboard")
            context = json.loads(row["payload_json"])
            operation(context)
            db.execute("UPDATE sessions SET payload_json=?, version=version+1 WHERE session_id=?", (json.dumps(context), session_id))
            return context


class DynamoRepository:
    """Optimistic concurrency protects each isolated session in cloud mode."""
    def __init__(self, table_name: str):
        import boto3
        self.table = boto3.resource("dynamodb").Table(table_name)

    def get(self, session_id: str) -> Context | None:
        row = self.table.get_item(Key={"session_id": session_id}, ConsistentRead=True).get("Item")
        if not row or int(row["expires_at"]) <= int(time.time()):
            return None
        return json.loads(row["payload_json"])

    def create(self, session_id: str, context: Context) -> None:
        ttl = int(time.time()) + int(os.getenv("JAL_SESSION_TTL_HOURS", "24")) * 3600
        self.table.put_item(Item={"session_id": session_id, "payload_json": json.dumps(context), "version": 1, "expires_at": ttl}, ConditionExpression="attribute_not_exists(session_id)")

    def mutate(self, session_id: str, operation: Mutation) -> Context:
        from botocore.exceptions import ClientError
        for _ in range(5):
            row = self.table.get_item(Key={"session_id": session_id}, ConsistentRead=True).get("Item")
            if not row or int(row["expires_at"]) <= int(time.time()):
                raise KeyError("Session expired; reload the dashboard")
            context = json.loads(row["payload_json"])
            operation(context)
            try:
                self.table.update_item(Key={"session_id": session_id}, UpdateExpression="SET payload_json=:payload, #v=:next", ConditionExpression="#v=:old", ExpressionAttributeNames={"#v": "version"}, ExpressionAttributeValues={":payload": json.dumps(context), ":next": int(row["version"]) + 1, ":old": int(row["version"])})
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
