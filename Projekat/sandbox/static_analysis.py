import ast
from pathlib import Path
from typing import TypeAlias

AnalysisResult: TypeAlias = tuple[bool, str]

FORBIDDEN_MODULES = {
    "os",
    "subprocess",
    "sys",
    "socket",
    "requests",
    "urllib",
    "shutil",
    "pathlib",
    "glob",
    "ctypes",
    "multiprocessing",
    "threading",
}

FORBIDDEN_BUILTINS = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "input",
}


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.violations: list[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split(".")[0]
            if module_name in FORBIDDEN_MODULES:
                self.violations.append(
                    f"Forbidden module import: '{module_name}' on line {node.lineno}"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module_name = node.module.split(".")[0]
            if module_name in FORBIDDEN_MODULES:
                self.violations.append(
                    f"Forbidden module import: '{module_name}' on line {node.lineno}"
                )
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_BUILTINS:
                self.violations.append(
                    f"Forbidden function call: '{func_name}()' on line {node.lineno}"
                )
        self.generic_visit(node)


def analyze_code(script_path: str | Path) -> AnalysisResult:
    path = Path(script_path)
    if not path.exists():
        return False, f"File does not exist: {path}"

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return False, f"Syntax error: {exc.msg} on line {exc.lineno}"
    except OSError as exc:
        return False, f"Cannot read file: {exc}"

    analyzer = CodeAnalyzer()
    analyzer.visit(tree)

    if analyzer.violations:
        reason = "Static analysis detected security issues:\n" + "\n".join(
            f"  - {violation}" for violation in analyzer.violations
        )
        return False, reason

    return True, ""


def analyze_python_file(script_path: str | Path) -> dict:
    is_safe, reason = analyze_code(script_path)
    findings = [
        line.strip(" -")
        for line in reason.splitlines()
        if line.strip() and not line.startswith("Static analysis")
    ]
    return {
        "allowed": is_safe,
        "findings": findings,
        "engine": "sandbox.static_analysis",
    }
