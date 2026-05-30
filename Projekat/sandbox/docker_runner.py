import hashlib
import subprocess
from pathlib import Path
from typing import Any

from . import limits

DOCKER_UNAVAILABLE_MARKERS = (
    "cannot connect to the docker daemon",
    "failed to connect to the docker api",
    "docker daemon is not running",
    "is the docker daemon running",
)


def run_in_docker(
    script_path: str,
    input_text: str | None = None,
    work_dir: str | None = None,
) -> dict[str, Any]:
    script = Path(script_path).resolve()
    if not script.exists():
        return {
            "stdout": "",
            "stderr": f"File does not exist: {script}",
            "timeout": False,
            "exit_code": 1,
        }

    root = Path(work_dir).resolve() if work_dir else script.parent
    try:
        container_script_path = script.relative_to(root).as_posix()
    except ValueError:
        return {
            "stdout": "",
            "stderr": f"Script path is not inside work_dir: {script}",
            "timeout": False,
            "exit_code": 1,
        }

    image = _prepare_image(root)
    if image["exit_code"] != 0:
        return image

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory",
        limits.MEMORY_LIMIT,
        "--cpus",
        str(limits.CPU_LIMIT),
        "--pids-limit",
        str(limits.PIDS_LIMIT),
        "--user",
        limits.USER_ID,
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=10m",
        "-v",
        f"{root}:/app:ro",
        "-w",
        "/app",
        image["image"],
        "python",
        container_script_path,
    ]

    try:
        result = subprocess.run(
            docker_cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=limits.TIMEOUT,
            check=False,
        )
        exit_code = result.returncode
        stderr = result.stderr or ""
        if _looks_like_docker_unavailable(stderr):
            exit_code = 127

        return {
            "stdout": result.stdout,
            "stderr": stderr,
            "timeout": False,
            "exit_code": exit_code,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Execution stopped: timeout of {limits.TIMEOUT} seconds exceeded",
            "timeout": True,
            "exit_code": 124,
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "Docker was not found. Install/start Docker and try again.",
            "timeout": False,
            "exit_code": 127,
        }
    except Exception as exc:
        return {
            "stdout": "",
            "stderr": f"Unexpected Docker execution error: {exc}",
            "timeout": False,
            "exit_code": 1,
        }


def _prepare_image(root: Path) -> dict[str, Any]:
    requirements = root / "requirements.txt"
    if not requirements.exists():
        return {"image": limits.DOCKER_IMAGE, "exit_code": 0, "stderr": ""}

    requirements_hash = hashlib.sha256(requirements.read_bytes()).hexdigest()[:16]
    image_name = f"{limits.DEPENDENCY_IMAGE_PREFIX}:{requirements_hash}"
    dockerfile = (
        f"FROM {limits.DOCKER_IMAGE}\n"
        "WORKDIR /app\n"
        "COPY requirements.txt /tmp/requirements.txt\n"
        "RUN pip install --no-cache-dir -r /tmp/requirements.txt\n"
    )

    try:
        result = subprocess.run(
            ["docker", "build", "-q", "-t", image_name, "-f", "-", str(root)],
            input=dockerfile,
            capture_output=True,
            text=True,
            timeout=limits.BUILD_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Dependency image build stopped: timeout of {limits.BUILD_TIMEOUT} seconds exceeded",
            "timeout": True,
            "exit_code": 124,
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "Docker was not found. Install/start Docker and try again.",
            "timeout": False,
            "exit_code": 127,
        }

    stderr = result.stderr or ""
    exit_code = result.returncode
    if _looks_like_docker_unavailable(stderr):
        exit_code = 127

    if exit_code != 0:
        return {
            "stdout": result.stdout,
            "stderr": stderr,
            "timeout": False,
            "exit_code": exit_code,
        }

    return {"image": image_name, "exit_code": 0, "stderr": ""}


def _looks_like_docker_unavailable(stderr: str) -> bool:
    lowered = stderr.lower()
    return any(marker in lowered for marker in DOCKER_UNAVAILABLE_MARKERS)
