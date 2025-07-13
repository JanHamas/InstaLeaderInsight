import sys
import os,random
import asyncio
import re
import traceback
import openpyxl
from groq import Groq 
from dotenv import load_dotenv
from config import settings
from data.input import config_input
from config.login import login_insta
from playwright.async_api import async_playwright
from util.bypass_captcha import check_and_solve_captcha
from util.helper import load_proxies


# load all var from .env file
load_dotenv

# this function are sending the user bio to ai for get TRUE/FALSE words base on provided criteria which in config_input.py
async def ai_profile_checker(ai_prompt: str, header_text: str) -> str | None:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    messages = [{"role": "user", "content": f"{ai_prompt}{header_text}"}]

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        response_text = completion.choices[0].message.content.strip()
        return response_text
    except Exception as e:
        print("\nError:", e)
        print(traceback.format_exc())
        return None

# this function are update excel file
def update_excel(row: list[str]) -> None:
    wb = openpyxl.load_workbook(settings.LEADS_FILE_PATH)
    sheet = wb.active
    sheet.append(row)
    wb.save(settings.LEADS_FILE_PATH)

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

# this is ma will be scrap programaticaly profile when ai give True word as a reponsive
async def scrap_profile(browser, usernames: list[str]) -> None:
    proxies = load_proxies(settings.PROXIES_FILE_PATH)
    random.shuffle(proxies)

    recording = settings.record_video.lower().strip() == "on"
    one_context_recording = False
    context = None

    # Try proxies until one works
    for proxy in proxies:
        try:
            context_options = {"proxy": proxy}

            if recording and not one_context_recording:
                context_options["record_video_dir"] = "videos"
                context_options["record_video_size"] = {"width": 1920, "height": 1080}

            context = await browser.new_context(**context_options)
            await login_insta(context)

            print(f"✅ Proxy working: {proxy['server']}")
            one_context_recording = True
            break
        except Exception as e:
            print(f"❌ Proxy failed: {proxy['server']} — {e}")
            continue

    if not context:
        print("❌ All proxies failed. Exiting.")
        return

    # Process each username
    for username in usernames:
        page = None
        try:
            page = await context.new_page()
            url = f"https://www.{username}/"
            await page.goto(url, wait_until="load", timeout=30000)
            await asyncio.sleep(float(settings.SLEEP_BETWEEN_PAGE_LOADS))

            await check_and_solve_captcha(page)

            locator = page.locator("header, .header, div[role='banner']").first
            profile_header_text = (await locator.inner_text()).lower()

            if not profile_header_text:
                await resave_username(username)
                continue

            await append_username(username)
            await remove_username(username)

            header_text = profile_header_text.strip().lower()

            should_check = any(k.lower() in header_text for k in config_input.LEADERSHIP_KEYWORDS)

            if not should_check:
                continue

            is_verified = False
            if config_input.is_verified.lower().strip() == "yes":
                verified_ele = page.locator("svg[aria-label='Verified']")
                is_verified = await verified_ele.count() > 0
                if not is_verified:
                    print("Not Verified")
                    continue

            ai_response = await ai_profile_checker(config_input.AI_PROMPT, profile_header_text)
            print("AI RESPONSE\n", ai_response)

            if ai_response.lower().strip() == "true":
                row = await copy_profile(page=page)
                update_excel(row)

        except Exception as e:
            print(f"⚠️ Error scraping {username}: {e}")
            await resave_username(username)

        finally:
            if page:
                try:
                    pages = context.pages
                    if len(pages) > 1:
                        await page.close()
                except Exception as e:
                    print(f"⚠️ Error while checking or closing page: {e}")

    # Clean up context
    await context.close()
    print("🧹 Context closed after processing chunk.")

# main funciton initialization browser and calling login function
async def every_profile_checker():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=settings.HEADLESS)

    username_chunks = split_usernames_into_chunks()

    tasks = []
    for chunk in username_chunks:
        # page = await context.new_page()
        # tasks.append(scrap_profile(page, chunk))
        tasks.append((scrap_profile(browser,chunk)))

    await asyncio.gather(*tasks)