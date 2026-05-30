import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

TOKEN_FILE = Path(".oblak_token")
DEFAULT_SERVER = "http://127.0.0.1:5000"


def read_token() -> str | None:
    if os.environ.get("OBLAK_TOKEN"):
        return os.environ["OBLAK_TOKEN"]
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    return None


def request_json(method: str, server: str, path: str, body=None, token: str | None = None):
    data = json.dumps(body or {}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        urljoin(server.rstrip("/") + "/", path.lstrip("/")),
        data=data,
        headers=headers,
        method=method,
    )
    return send(request)


def request_multipart(server: str, path: str, fields: dict, files: dict, token: str):
    boundary = "----oblak-boundary"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for name, file_path in files.items():
        path_obj = Path(file_path)
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{path_obj.name}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
        )
        body.extend(path_obj.read_bytes())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode())
    request = Request(
        urljoin(server.rstrip("/") + "/", path.lstrip("/")),
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    return send(request)


def send(request: Request):
    try:
        with urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except json.JSONDecodeError:
            payload = {"error": exc.reason}
        return exc.code, payload
    except URLError as exc:
        raise SystemExit(f"Cannot reach server: {exc.reason}") from exc


def print_response(status: int, payload: dict):
    print(json.dumps({"status": status, **payload}, indent=2))
    return 0 if 200 <= status < 300 else 1


def register(args):
    status, payload = request_json(
        "POST",
        args.server,
        "/auth/register",
        {"username": args.username, "password": args.password},
    )
    if "api_token" in payload:
        TOKEN_FILE.write_text(payload["api_token"], encoding="utf-8")
    return print_response(status, payload)


def login(args):
    status, payload = request_json(
        "POST",
        args.server,
        "/auth/login",
        {"username": args.username, "password": args.password},
    )
    if "api_token" in payload:
        TOKEN_FILE.write_text(payload["api_token"], encoding="utf-8")
    return print_response(status, payload)


def upload(args):
    token = read_token()
    if not token:
        raise SystemExit("Login first or set OBLAK_TOKEN.")

    files = {"code": args.code}
    if args.requirements:
        files["requirements"] = args.requirements

    status, payload = request_multipart(
        args.server,
        "/functions",
        {"name": args.name, "entrypoint": Path(args.code).name},
        files,
        token,
    )
    return print_response(status, payload)


def run(args):
    status, payload = request_json("POST", args.server, f"/run/{args.function_id}", args.payload)
    return print_response(status, payload)


def build_parser():
    parser = argparse.ArgumentParser(prog="cdk", description="Oblak CDK CLI")
    parser.add_argument("--server", default=DEFAULT_SERVER)
    subparsers = parser.add_subparsers(required=True)

    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("username")
    register_parser.add_argument("password")
    register_parser.set_defaults(func=register)

    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("username")
    login_parser.add_argument("password")
    login_parser.set_defaults(func=login)

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("name")
    upload_parser.add_argument("code")
    upload_parser.add_argument("--requirements")
    upload_parser.set_defaults(func=upload)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("function_id")
    run_parser.add_argument("--payload", type=json.loads, default={})
    run_parser.set_defaults(func=run)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
