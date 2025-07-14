import aioimaplib
import re,os
from email import message_from_bytes
import asyncio
from config import settings
import asyncio
import re
import openpyxl
from config import settings
import ctypes
import random
from playwright.async_api import BrowserContext


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

# append checked usernames.txt file for avoid duplicate
async def append_username(username):
        try:
            # Read existing usernames from the file
            if os.path.exists(settings.CHECKED_USERNAMES_FILE_PATH):
                with open(settings.CHECKED_USERNAMES_FILE_PATH, 'r', encoding='utf-8') as f:
                    checked_usernames = set(line.strip() for line in f)
            else:
                checked_usernames = set()

            # Only append if the username is not already saved
            if username not in checked_usernames:
                with open(settings.CHECKED_USERNAMES_FILE_PATH, 'a', encoding='utf-8') as f:
                    f.write(username + "\n")
                    f.flush()
        except Exception as e:
            print(e)

# remove those username from usernames.txt which we have checked there profile 
async def remove_username(username):
    try:
        # Remove the username from usernames.txt
        with open(settings.USERNAMES_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        lines = set(line for line in lines if line.strip() != username)
        with open(settings.USERNAMES_FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            f.flush()
    except Exception as e:
        print(e)

# resave the username sometime error accure to scrap/check user profle so we resave there username in usernames.txt
async def resave_username(username):
    try:
        with open(settings.USERNAMES_FILE_PATH,"a") as f:
            f.write(username + "\n")
            f.flush()
            # print("Sucessfully Resaved Username!")
    except Exception as e:
        print(e)



# user agents 
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SAMSUNG SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.0 Chrome/92.0.4515.166 Mobile Safari/537.36",
]

# this function are update excel file
async def update_excel(row: list[str]) -> None:
    wb = openpyxl.load_workbook(settings.LEADS_FILE_PATH)
    sheet = wb.active
    sheet.append(row)
    wb.save(settings.LEADS_FILE_PATH)
    print("✅ Saved in excel!")

# This function are split usernames from usernames.txt in to chunk for parallel execution on multiple tabs
def split_usernames_into_chunks(chunk_count=settings.chunk_size) -> list[list[str]]:
    if not os.path.exists(settings.USERNAMES_FILE_PATH):
        raise FileNotFoundError(f"File not found: {settings.USERNAMES_FILE_PATH}")

    with open(settings.USERNAMES_FILE_PATH, 'r', encoding='utf-8') as f:
        usernames = [line.strip() for line in f if line.strip()]

    total = len(usernames)
    chunk_size = (total + chunk_count - 1) // chunk_count  # Ceiling division

    chunks = [usernames[i:i + chunk_size] for i in range(0, total, chunk_size)]

    # Pad with empty lists if less than chunk_count
    while len(chunks) < chunk_count:
        chunks.append([])

    return chunks

# this function are calling in scrap_profile and they are programaticaly extract user profile name etc
async def copy_profile(page):
    # Get complete header text (bio, contact info, etc.)
    complete_header_ele = page.locator("header, .header, div[role='banner']")
    complete_header_text = await complete_header_ele.inner_text()

    # Name from <h2><span>
    name = await page.locator('div.x15mokao > span[dir="auto"] >> nth=0').inner_text()

    # bio only
    bio = await page.locator('section:has(div:has-text("posts")) + section').inner_text()

    # Username from URL
    # username = page.url.rstrip('/').split('/')[-1]

    # Locate the element containing posts, followers, and following (usually a <ul>)
    pff_locator = page.locator("ul:has-text('followers')")

    # Make sure we get the first matching element safely
    pff_text = await pff_locator.first.inner_text()

    # Extract numbers (handles comma and K/M notation)
    def parse_count(text):
        if 'K' in text:
            return int(float(text.replace('K', '').replace(',', '')) * 1_000)
        elif 'M' in text:
            return int(float(text.replace('M', '').replace(',', '')) * 1_000_000)
        else:
            return int(text.replace(',', ''))

    # Match patterns like "2,862", "20.5K", "7.7M"
    matches = re.findall(r'[\d.,]+[KM]?', pff_text)
    pff_numbers = [parse_count(m) for m in matches]

    # Assign values safely
    post_count = pff_numbers[0] if len(pff_numbers) > 0 else 0
    followers = pff_numbers[1] if len(pff_numbers) > 1 else 0
    following = pff_numbers[2] if len(pff_numbers) > 2 else 0
    # Contact info
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', complete_header_text)
    phones = re.findall(r'(\+?\d[\d\s().-]{7,}\d)', complete_header_text)
    contacts = emails + phones
    contact_str = ", ".join(contacts)

    # Websites regex pattern
    websites_pattern = re.compile(
        r'(https?://[^\s,]+|'                 # full http(s) links
        r'www\.[^\s,]+|'                      # www based links
        r'[a-zA-Z0-9.-]+\.(com|io|ai|co|org|net|me|vc|app|link|tv|to|ly)(/[^\s,]*)?)'  # domain patterns
    )
    # Find all matches
    matches = websites_pattern.findall(complete_header_text)

    # Extract only the full matched strings
    extracted_urls = [match[0] if isinstance(match, tuple) else match for match in matches]

    # Clean up any trailing punctuation and join as a string
    website_str = "\n ".join([url.rstrip('.,') for url in extracted_urls])

    # all header section (remove contacts and websites from it if needed)
    all_info = complete_header_text.strip()

    # Final row in order of: Name, Username, Post Count, Followers, Following, Phone/Email, Website, Bio
    username = page.url
    print([name, username, post_count, followers, following, contact_str, website_str, bio, all_info])
    return [name, username, post_count, followers, following, contact_str, website_str, bio, all_info]

# Prevent display to off
def prevent_display_off():
    # Prevent the system from sleeping or turning off the display
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )

# renable default sleep behavior
def enable_default_sleep_behavior():
    # Re-enable normal sleep behavior
    ES_CONTINUOUS = 0x80000000
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

async def humanize_behave_on_page(page):
    try:
        width, height = await page.evaluate("() => [window.innerWidth, window.innerHeight]")

        # Random mouse move
        for _ in range(random.randint(3, 6)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            await asyncio.sleep(random.uniform(0.1, 0.3))

        # Random scroll up/down
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 600)
            await page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.2, 0.4))

        # print("🤖 Simulated human behavior")
    except Exception as e:
        print(f"[!] Humanization failed: {e}")

# 
async def switch_tab(context):
    pages = context.pages
    if len(pages) <= 1:
        print("⚠️ Only one tab open. No switch needed.")
        return

    # Identify the current active tab (usually the last opened/focused one)
    current_page = None
    for page in pages:
        if await page.evaluate("document.hasFocus()"):
            current_page = page
            break

    # If no page has focus, default to index 0
    current_index = pages.index(current_page) if current_page else 0
    next_index = (current_index + 1) % len(pages)

    await pages[next_index].bring_to_front()
    print(f"🌀 Switched to tab {next_index + 1}")

import os
from playwright.async_api import BrowserContext


def delete_all_except_latest_two(folder_path: str):
    # Get all .webm files (video recordings) with full paths
    files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith('.webm')
    ]

    # Sort by modified time descending (latest first)
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    # Keep the latest two, delete the rest
    files_to_delete = files[2:]

    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"🗑️ Deleted: {file}")
        except Exception as e:
            print(f"⚠️ Error deleting {file}: {e}")

async def close_context_and_keep_latest_two(context: BrowserContext, folder_path: str):
    # Delete old recordings first
    delete_all_except_latest_two(folder_path)

    # Close the browser context
    if context:
        await context.close()
        print("✅ Browser context closed.")





