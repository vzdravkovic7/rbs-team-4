import ast
import os
from typing import Tuple

FORBIDDEN_MODULES = {
    'os',
    'subprocess',
    'sys',
    'socket',
    'requests',
    'urllib',
    'shutil',
    'pathlib',
    'glob',
    'ctypes',
    'multiprocessing',
    'threading'
}

FORBIDDEN_BUILTINS = {
    'eval',
    'exec',
    'compile',
    'open',
    '__import__',
    'input',
}


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
    
    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name in FORBIDDEN_MODULES:
                self.violations.append(
                    f"Zabranjen import modula: '{module_name}' na liniji {node.lineno}"
                )
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in FORBIDDEN_MODULES:
                self.violations.append(
                    f"Zabranjen import iz modula: '{module_name}' na liniji {node.lineno}"
                )
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_BUILTINS:
                self.violations.append(
                    f"Zabranjena funkcija: '{func_name}()' na liniji {node.lineno}"
                )
        self.generic_visit(node)


def analyze_code(script_path: str) -> Tuple[bool, str]:
    if not os.path.exists(script_path):
        return False, f"Fajl ne postoji: {script_path}"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        tree = ast.parse(code, filename=script_path)
        
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        
        if analyzer.violations:
            reason = "Statička analiza je detektovala bezbednosne probleme:\n" + \
                     "\n".join(f"  - {v}" for v in analyzer.violations)
            return False, reason
        
        return True, ""
    
    except SyntaxError as e:
        return False, f"Sintaksna greška u kodu: {str(e)}"
    
    except Exception as e:
        return False, f"Greška tokom analize: {str(e)}"

if __name__ == "__main__":
    test_file = "test_scripts/malicious/os_system.py"
    is_safe, reason = analyze_code(test_file)
    
    if is_safe:
        print(f"✓ Kod je bezbedan: {test_file}")
    else:
        print(f"✗ Kod nije bezbedan: {test_file}")
        print(reason)