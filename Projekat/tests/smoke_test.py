import io
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import app  # noqa: E402


def main():
    client = app.test_client()
    username = f"student-{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/auth/register",
        json={"username": username, "password": "password123"},
    )
    assert response.status_code == 201, response.json
    token = response.json["api_token"]

    response = client.post(
        "/functions",
        data={
            "name": "hello",
            "entrypoint": "main.py",
            "code": (io.BytesIO(b'print("hello from oblak")'), "main.py"),
        },
        headers={"Authorization": f"Bearer {token}"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.json
    function_id = response.json["id"]

    response = client.post(f"/run/{function_id}", json={"x": 1})
    assert response.status_code == 200, response.json
    assert "hello from oblak" in response.json["stdout"]

    response = client.post(
        "/functions",
        data={
            "name": "bad",
            "entrypoint": "bad.py",
            "code": (io.BytesIO(b"import os\nprint(os.getcwd())"), "bad.py"),
        },
        headers={"Authorization": f"Bearer {token}"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400, response.json
    assert response.json["status"] == "rejected"

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
