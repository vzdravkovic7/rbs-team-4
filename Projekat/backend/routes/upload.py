import json
import shutil
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request, url_for
from werkzeug.utils import secure_filename

from analysis import analyze_python_file
from audit import audit
from auth_required import auth_required
from database.db import get_connection

upload_bp = Blueprint("upload", __name__, url_prefix="/functions")

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
ALLOWED_CODE_EXTENSIONS = {".py"}


@upload_bp.post("")
@auth_required
def upload_function(current_user):
    code_file = request.files.get("code")
    requirements_file = request.files.get("requirements")
    name = (request.form.get("name") or "").strip()
    entrypoint = (request.form.get("entrypoint") or "main.py").strip()

    if not code_file or not name:
        return jsonify({"error": "Fields 'name' and file 'code' are required"}), 400

    code_name = secure_filename(code_file.filename or "")
    if Path(code_name).suffix not in ALLOWED_CODE_EXTENSIONS:
        return jsonify({"error": "Only single .py uploads are supported by this backend part"}), 400

    function_id = str(uuid.uuid4())
    function_dir = UPLOAD_DIR / function_id
    function_dir.mkdir(parents=True, exist_ok=False)

    stored_code = function_dir / entrypoint
    code_file.save(stored_code)

    requirements_name = None
    if requirements_file and requirements_file.filename:
        requirements_name = "requirements.txt"
        requirements_file.save(function_dir / requirements_name)

    report = analyze_python_file(stored_code)
    status = "ready" if report["allowed"] else "rejected"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO functions
                (id, owner_id, name, entrypoint, requirements_file, status, analysis_report, storage_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                function_id,
                current_user["id"],
                name,
                entrypoint,
                requirements_name,
                status,
                json.dumps(report),
                str(function_dir),
            ),
        )

    audit(
        "function_uploaded",
        user_id=current_user["id"],
        function_id=function_id,
        status=status,
        findings=report["findings"],
    )

    if status == "rejected":
        shutil.rmtree(function_dir, ignore_errors=True)

    return (
        jsonify(
            {
                "id": function_id,
                "name": name,
                "status": status,
                "analysis": report,
                "run_url": url_for("run.run_function", function_id=function_id, _external=True),
            }
        ),
        201 if status == "ready" else 400,
    )
