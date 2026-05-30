import json
import sys
from pathlib import Path

from flask import Blueprint, jsonify, request

from audit import audit
from database.db import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sandbox.executor import run_user_code

run_bp = Blueprint("run", __name__, url_prefix="/run")


def load_function(function_id: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM functions WHERE id = ?",
            (function_id,),
        ).fetchone()
    return dict(row) if row else None


@run_bp.post("/<function_id>")
def run_function(function_id):
    function = load_function(function_id)
    if not function:
        return jsonify({"error": "Function not found"}), 404

    if function["status"] != "ready":
        return jsonify({"error": "Function is not ready", "status": function["status"]}), 409

    function_dir = Path(function["storage_path"])
    entrypoint = function_dir / function["entrypoint"]
    payload = request.get_json(silent=True) or {}

    result = run_user_code(
        str(entrypoint),
        input_text=json.dumps(payload),
        work_dir=str(function_dir),
    )

    if result["blocked_by_policy"]:
        audit("function_blocked", function_id=function_id, reason=result["reason"])
        return jsonify({"error": "Blocked by sandbox policy", **result}), 403

    if result["timeout"]:
        audit("function_timeout", function_id=function_id)
        return jsonify({"error": "Execution timed out"}), 504

    if result["exit_code"] == 127:
        audit("sandbox_unavailable", function_id=function_id, stderr=result["stderr"])
        return jsonify({"error": "Sandbox unavailable", **result}), 503

    audit(
        "function_executed",
        function_id=function_id,
        return_code=result["exit_code"],
    )
    return (
        jsonify(
            {
                "return_code": result["exit_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "sandbox": {
                    "blocked_by_policy": result["blocked_by_policy"],
                    "reason": result["reason"],
                    "timeout": result["timeout"],
                },
            }
        ),
        200 if result["exit_code"] == 0 else 500,
    )
