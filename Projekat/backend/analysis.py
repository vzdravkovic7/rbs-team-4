import ast
from pathlib import Path

BANNED_IMPORTS = {"os", "socket", "subprocess", "ctypes", "multiprocessing"}
BANNED_CALLS = {"eval", "exec", "open", "__import__"}


def analyze_python_file(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    findings: list[str] = []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {
            "allowed": False,
            "findings": [f"Syntax error: {exc.msg} on line {exc.lineno}"],
        }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in BANNED_IMPORTS:
                    findings.append(f"Banned import: {alias.name}")

        if isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root in BANNED_IMPORTS:
                findings.append(f"Banned import: {node.module}")

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
                findings.append(f"Banned call: {node.func.id}")

    return {"allowed": not findings, "findings": findings}
