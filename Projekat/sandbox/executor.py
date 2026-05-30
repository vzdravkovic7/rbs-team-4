import os
import datetime
from typing import Dict
from sandbox.static_analysis import analyze_code
from sandbox.docker_runner import run_in_docker

AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(__file__),
    'logs',
    'audit.log'
)


def ensure_log_directory():
    log_dir = os.path.dirname(AUDIT_LOG_PATH)
    os.makedirs(log_dir, exist_ok=True)


def log_execution(script_path: str, result: Dict, blocked: bool = False):
    ensure_log_directory()
    
    timestamp = datetime.datetime.now().isoformat()
    
    if blocked:
        status = "BLOCKED"
        details = result.get('reason', 'Nepoznat razlog')
    elif result.get('timeout', False):
        status = "TIMEOUT"
        details = f"Prekoračen limit od {result.get('timeout')} sekundi"
    elif result.get('exit_code', 0) == 0:
        status = "SUCCESS"
        details = "Uspešno izvršeno"
    else:
        status = "ERROR"
        details = f"Exit code: {result.get('exit_code')}, stderr: {result.get('stderr', '')[:100]}"
    
    log_line = f"[{timestamp}] {status} | Script: {script_path} | Details: {details}\n"
    
    try:
        with open(AUDIT_LOG_PATH, 'a', encoding='utf-8') as log_file:
            log_file.write(log_line)
    except Exception as e:
        print(f"UPOZORENJE: Nije moguće pisati u audit log: {e}")


def run_user_code(script_path: str) -> Dict[str, any]:
    if not os.path.exists(script_path):
        error_result = {
            'success': False,
            'stdout': '',
            'stderr': f'Fajl ne postoji: {script_path}',
            'blocked_by_policy': False,
            'reason': 'Fajl ne postoji',
            'timeout': False,
            'exit_code': 1
        }
        log_execution(script_path, error_result, blocked=True)
        return error_result
    
    print(f"[Sandbox] Pokrećem statičku analizu za: {script_path}")
    is_safe, reason = analyze_code(script_path)
    
    if not is_safe:
        print(f"[Sandbox] ✗ Kod nije bezbedan: {reason}")
        
        blocked_result = {
            'success': False,
            'stdout': '',
            'stderr': '',
            'blocked_by_policy': True,
            'reason': reason,
            'timeout': False,
            'exit_code': 1
        }
        
        log_execution(script_path, blocked_result, blocked=True)
        
        return blocked_result
    
    print(f"[Sandbox] ✓ Statička analiza prošla, pokrećem Docker kontejner...")
    
    docker_result = run_in_docker(script_path)
    
    success = (docker_result['exit_code'] == 0) and (not docker_result['timeout'])
    
    final_result = {
        'success': success,
        'stdout': docker_result['stdout'],
        'stderr': docker_result['stderr'],
        'blocked_by_policy': False,
        'reason': '' if success else (
            'Timeout' if docker_result['timeout'] else 'Runtime error'
        ),
        'timeout': docker_result['timeout'],
        'exit_code': docker_result['exit_code']
    }
    
    log_execution(script_path, final_result, blocked=False)
    
    if success:
        print(f"[Sandbox] ✓ Uspešno izvršeno")
    else:
        print(f"[Sandbox] ✗ Greška: {final_result['reason']}")
    
    return final_result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_script = sys.argv[1]
    else:
        test_script = "test_scripts/benign/hello.py"
    
    print(f"\n{'='*60}")
    print(f"SANDBOX EXECUTOR TEST")
    print(f"{'='*60}\n")
    
    result = run_user_code(test_script)
    
    print(f"\n{'='*60}")
    print(f"REZULTAT")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Blocked: {result['blocked_by_policy']}")
    
    if result['stdout']:
        print(f"\nStdout:\n{result['stdout']}")
    
    if result['stderr']:
        print(f"\nStderr:\n{result['stderr']}")
    
    if result['reason']:
        print(f"\nReason: {result['reason']}")