import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any

from sandbox.docker_runner import run_in_docker
from sandbox.static_analysis import analyze_code

AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(__file__),
    "logs",
    "audit.log",
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def ensure_log_directory():
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)


def log_execution(script_path: str, result: dict[str, Any], blocked: bool = False):
    ensure_log_directory()

    if blocked:
        event = "sandbox_execution_blocked"
    elif result.get("timeout", False):
        event = "sandbox_execution_timeout"
    elif result.get("exit_code", 0) == 0:
        event = "sandbox_execution_success"
    else:
        event = "sandbox_execution_error"

    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": event,
        "script_path": _display_path(script_path),
        "success": result.get("success", False),
        "blocked_by_policy": result.get("blocked_by_policy", False),
        "timeout": result.get("timeout", False),
        "exit_code": result.get("exit_code"),
        "reason": result.get("reason", ""),
    }

    stderr = result.get("stderr", "")
    if stderr:
        record["stderr_summary"] = stderr[:200]

    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        logger.exception("Cannot write sandbox audit log")


def _display_path(path: str) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def run_user_code(
    script_path: str,
    input_text: str | None = None,
    work_dir: str | None = None,
) -> dict[str, Any]:
    if not os.path.exists(script_path):
        error_result = _execution_result(
            success=False,
            stderr=f"File does not exist: {script_path}",
            reason="File does not exist",
            exit_code=1,
        )
        log_execution(script_path, error_result, blocked=True)
        return error_result

    is_safe, reason = analyze_code(script_path)
    if not is_safe:
        blocked_result = _execution_result(
            success=False,
            blocked_by_policy=True,
            reason=reason,
            exit_code=1,
        )
        log_execution(script_path, blocked_result, blocked=True)
        return blocked_result

    docker_result = run_in_docker(script_path, input_text=input_text, work_dir=work_dir)
    success = docker_result["exit_code"] == 0 and not docker_result["timeout"]
    final_result = _execution_result(
        success=success,
        stdout=docker_result["stdout"],
        stderr=docker_result["stderr"],
        reason="" if success else ("Timeout" if docker_result["timeout"] else "Runtime error"),
        timeout=docker_result["timeout"],
        exit_code=docker_result["exit_code"],
    )

    log_execution(script_path, final_result, blocked=False)
    return final_result


def _execution_result(
    *,
    success: bool,
    stdout: str = "",
    stderr: str = "",
    blocked_by_policy: bool = False,
    reason: str = "",
    timeout: bool = False,
    exit_code: int = 0,
) -> dict[str, Any]:
    return {
        "success": success,
        "stdout": stdout,
        "stderr": stderr,
        "blocked_by_policy": blocked_by_policy,
        "reason": reason,
        "timeout": timeout,
        "exit_code": exit_code,
    }
