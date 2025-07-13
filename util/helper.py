import aioimaplib
import re
from email import message_from_bytes
import asyncio


# Get the latest Instagram OTP from Gmail
async def get_latest_instagram_otp(email_user, email_pass, timeout=50):
    try:
        client = aioimaplib.IMAP4_SSL('imap.gmail.com', 993)
        await client.wait_hello_from_server()
        await client.login(email_user, email_pass)
        await client.select('INBOX')

        print("📬 Checking for Instagram OTP email...")
        otp = None
        end_time = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < end_time:
            resp = await client.search('UNSEEN FROM "security@mail.instagram.com"')
            email_ids = resp.lines[0].decode().split()
            if email_ids:
                latest = email_ids[-1]
                fetch_resp = await client.fetch(latest, '(RFC822)')
                raw = b'\n'.join(fetch_resp.lines[1:-1])
                msg = message_from_bytes(raw)

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                match = re.search(r'\b(\d{6})\b', body)
                if match:
                    otp = match.group(1)
                    print(f"✅ OTP found: {otp}")
                    break
                else:
                    print("⚠️ Email received, but OTP not found. Retrying...")
            else:
                print("⏳ No new OTP email. Waiting...")
            
            await asyncio.sleep(3)

        await client.logout()
        return otp

    except Exception as e:
        print(f"❌ IMAP error: {e}")
        return None


# Load proxies from file
def load_proxies(path):
    proxies = []
    with open(path, 'r') as file:
        for line in file:
            parts = line.strip().split(":")
            if len(parts) == 4:
                ip, port, user, pwd = parts
                proxies.append({
                    "server": f"http://{ip}:{port}",
                    "username": user,
                    "password": pwd
                })
    return proxies