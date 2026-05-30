import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sandbox.executor import run_user_code


def main():
    if len(sys.argv) < 2:
        print("❌ Greška: Nedostaje putanja do skripta!")
        print("\nUpotreba:")
        print("  python run_test.py <putanja_do_skripta>")
        print("\nPrimeri:")
        print("  python run_test.py sandbox/test_scripts/benign/hello.py")
        print("  python run_test.py sandbox/test_scripts/malicious/os_system.py")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    if not os.path.exists(script_path):
        print(f"❌ Fajl ne postoji: {script_path}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"  SANDBOX EXECUTOR - TEST")
    print(f"{'='*70}\n")
    
    result = run_user_code(script_path)
    
    print(f"\n{'='*70}")
    print(f"  REZULTAT")
    print(f"{'='*70}\n")
    
    if result['blocked_by_policy']:
        print(f"🚫 BLOKIRAN - {result['reason']}")
    elif result['timeout']:
        print(f"⏱️  TIMEOUT")
    elif result['success']:
        print(f"✅ USPEŠNO")
        if result['stdout']:
            print(f"\nOutput:\n{result['stdout']}")
    else:
        print(f"❌ GREŠKA")
        if result['stderr']:
            print(f"\nError:\n{result['stderr']}")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()