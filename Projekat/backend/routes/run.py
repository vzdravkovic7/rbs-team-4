import json
import subprocess
import sys
from pathlib import Path

from flask import Blueprint, jsonify, request

from audit import audit
from database.db import get_connection

run_bp = Blueprint("run", __name__, url_prefix="/run")

EXECUTION_TIMEOUT_SECONDS = 5


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

    try:
        result = subprocess.run(
            [sys.executable, str(entrypoint)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=function_dir,
            timeout=EXECUTION_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        audit("function_timeout", function_id=function_id)
        return jsonify({"error": "Execution timed out"}), 504

    audit(
        "function_executed",
        function_id=function_id,
        return_code=result.returncode,
    )
    return (
        jsonify(
            {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        ),
        200 if result.returncode == 0 else 500,
    )
