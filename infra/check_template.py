"""Offline structural checks; this does not transform SAM or validate an AWS account."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys

import yaml


def check(template_path: Path, check_source: bool = False) -> dict[str, object]:
    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(isinstance(template, dict), "Template must contain an object")
    if not isinstance(template, dict):
        return {"status": "FAIL", "failures": failures}

    require(template.get("Transform") == "AWS::Serverless-2016-10-31", "Missing SAM transform")
    resources = template.get("Resources", {})
    function = resources.get("JalApiFunction", {}).get("Properties", {})
    table = resources.get("SessionTable", {}).get("Properties", {})
    api = resources.get("HttpApi", {}).get("Properties", {})
    env = function.get("Environment", {}).get("Variables", {})
    require(function.get("Runtime") == "python3.13", "Runtime must match Python 3.13")
    require(function.get("Handler") == "app.main.handler", "Lambda handler must match the backend")
    require(function.get("CodeUri") == "../backend", "CodeUri must resolve to packaged backend")
    require(env.get("JAL_STORAGE") == "dynamodb", "Cloud state must not use SQLite")
    require(env.get("JAL_TABLE_NAME") == {"Ref": "SessionTable"}, "Session table environment is not wired")
    require(env.get("JAL_COOKIE_SECURE") == "true", "Cloud sessions require secure cookies")
    require(env.get("JAL_DEMO_ONLY") == "true", "Cloud template is restricted to simulated sessions")
    require(table.get("KeySchema") == [{"AttributeName": "session_id", "KeyType": "HASH"}], "Session partition key mismatch")
    require(table.get("TimeToLiveSpecification") == {"AttributeName": "expires_at", "Enabled": True}, "Session TTL mismatch")
    require(table.get("BillingMode") == "PAY_PER_REQUEST", "Unexpected provisioned capacity")
    require(function.get("Policies") == [{"DynamoDBCrudPolicy": {"TableName": {"Ref": "SessionTable"}}}], "Unexpected cloud permissions")
    require(not any(v.get("Type") == "AWS::SNS::Topic" for v in resources.values()), "No external notification route is implemented")
    cors = api.get("CorsConfiguration", {})
    require(cors.get("AllowOrigins") == [{"Ref": "AllowedOrigin"}], "Use the exact frontend origin")
    require(cors.get("AllowCredentials") is True, "Cookie sessions require credentialed CORS")
    require("X-CSRF-Token" in cors.get("AllowHeaders", []), "CSRF header is missing")
    require("ApiBaseUrl" in template.get("Outputs", {}), "Missing deployed API output")

    source_checks = "NOT_RUN"
    if check_source:
        code_root = (template_path.parent / str(function.get("CodeUri", ""))).resolve()
        main = code_root / "app" / "main.py"
        requirements = code_root / "requirements.txt"
        require(main.is_file(), "backend/app/main.py does not exist")
        require(requirements.is_file(), "backend/requirements.txt does not exist")
        if main.is_file():
            try:
                tree = ast.parse(main.read_text(encoding="utf-8"))
                bindings = {
                    target.id
                    for node in tree.body
                    if isinstance(node, ast.Assign)
                    for target in node.targets
                    if isinstance(target, ast.Name)
                }
                bindings.update(
                    node.target.id for node in tree.body
                    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                )
                require("handler" in bindings, "main.py has no global Lambda handler binding")
            except SyntaxError as error:
                require(False, f"main.py syntax error: {error.msg}")
        source_checks = "STATIC_AST_ONLY"

    return {
        "status": "FAIL" if failures else "PASS",
        "check_kind": "OFFLINE_STRUCTURE_ONLY",
        "source_checks": source_checks,
        "sam_transform": "NOT_RUN",
        "linux_dependency_build": "NOT_RUN",
        "aws_deployment": "NOT_RUN",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=Path(__file__).with_name("template.yaml"))
    parser.add_argument("--check-source", action="store_true")
    args = parser.parse_args()
    result = check(args.template, args.check_source)
    print(json.dumps(result, indent=2))
    return int(result["status"] != "PASS")


if __name__ == "__main__":
    sys.exit(main())
