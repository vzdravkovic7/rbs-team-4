import subprocess
import os
from typing import Dict
from . import limits


def run_in_docker(script_path: str) -> Dict[str, any]:
    if not os.path.exists(script_path):
        return {
            'stdout': '',
            'stderr': f'Fajl ne postoji: {script_path}',
            'timeout': False,
            'exit_code': 1
        }
    
    abs_script_path = os.path.abspath(script_path)
    
    container_script_path = "/app/user_script.py"
    
    docker_cmd = [
        'docker', 'run',
        '--rm',
        '--network', 'none',
        '--memory', limits.MEMORY_LIMIT,
        '--cpus', str(limits.CPU_LIMIT),
        '--user', limits.USER_ID,
        '--read-only',
        '--tmpfs', '/tmp:rw,noexec,nosuid,size=10m',
        '-v', f'{abs_script_path}:{container_script_path}:ro',
        limits.DOCKER_IMAGE,
        'python', container_script_path
    ]
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=limits.TIMEOUT
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'timeout': False,
            'exit_code': result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': f'Izvršavanje prekinuto: premašen timeout od {limits.TIMEOUT} sekundi',
            'timeout': True,
            'exit_code': 124
        }
    
    except FileNotFoundError:
        return {
            'stdout': '',
            'stderr': 'Greška: Docker nije pronađen. Da li je Docker instaliran i pokrenut?',
            'timeout': False,
            'exit_code': 127
        }
    
    except Exception as e:
        return {
            'stdout': '',
            'stderr': f'Neočekivana greška tokom izvršavanja: {str(e)}',
            'timeout': False,
            'exit_code': 1
        }

if __name__ == "__main__":
    test_script = "test_scripts/benign/hello.py"
    
    print(f"Pokrećem skript: {test_script}")
    result = run_in_docker(test_script)
    
    print("\n--- REZULTAT ---")
    print(f"Exit Code: {result['exit_code']}")
    print(f"Timeout: {result['timeout']}")
    print(f"\nStdout:\n{result['stdout']}")
    
    if result['stderr']:
        print(f"\nStderr:\n{result['stderr']}")