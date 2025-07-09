import sys
import os
import random
import asyncio
import re
import traceback
import openpyxl
from groq import Groq 
from dotenv import load_dotenv
import pyautogui
import time
from aioconsole import ainput  # Async input library

# load all var from .env file
load_dotenv

# Add the project root to sys.path so 'config' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings
from core.browser import get_browser_and_context
from data.input import config_input

async def check_using_ai(ai_prompt: str, header_text: str) -> str | None:
    client = Groq(api_key='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')
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


def update_excel(row: list[str]) -> None:
    wb = openpyxl.load_workbook(settings.LEADS_FILE_PATH)
    sheet = wb.active
    sheet.append(row)
    wb.save(settings.LEADS_FILE_PATH)


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


async def pause_for_user():
    await ainput("Change VPN and press Enter to continue: ")

async def check_profile_using_ai(page, usernames: list[str]) -> None:
    global username
    for username in usernames:
        url = f"https://www.{username}/"
        try:
            await page.goto(url, wait_until="load", timeout=12000)
            await page.wait_for_timeout(settings.SLEEP_BETWEEN_PAGE_LOADS)

            # Inside your main function/loop:
            content = await page.content()
            if "There's an issue and the page could not be loaded." in content:
                await pause_for_user()
                content = await page.content()  # Re-check after VPN change
                # Optional: retry or continue
                continue


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


            # Remove the username from usernames.txt
            with open(settings.USERNAMES_FILE_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            lines = [line for line in lines if line.strip() != username]
            with open(settings.USERNAMES_FILE_PATH, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            try:
                locator = page.locator("header, .header, div[role='banner']").first
                try:
                    profile_header_text = (await locator.inner_text()).lower()
                except Exception as e:
                    print("Error extracting header text:", e)
                    profile_header_text = ""
                
                if config_input.is_verified.lower().strip() == "yes":
                    # first check if profile verified if yes process otherwise skip
                    verified_ele = page.locator("svg[aria-label='Verified']")
                    try:
                        if await verified_ele.count() > 0:
                            is_verified = True
                        else:
                            print("Not Verified")
                            is_verified = False
                    except Exception as e:
                        print(f"Error processing profile: {e}")
                        is_verified = False  # ensure it's always defined
                    print(is_verified)
                    if  is_verified and any(words.lower().strip() in profile_header_text for words in config_input.LEADERSHIP_KEYWORDS):
                        print(is_verified)
                        print(username)
                        with open("complete_prompt.txt", 'w', encoding='utf-8') as f:
                            f.write(config_input.AI_PROMPT + "\n" + profile_header_text)

                        ai_response = await check_using_ai(config_input.AI_PROMPT, profile_header_text)
                        
                        print("AI RESPONSE","\n",ai_response)

                        if "false" in ai_response.lower():
                            pass
                        elif str(ai_response.lower().strip()) == "true":
                            row = await copy_profile(page=page)
                            update_excel(row)
                else:
                    if  any(words.lower().strip() in profile_header_text for words in config_input.LEADERSHIP_KEYWORDS):
                        print(username)
                        with open("complete_prompt.txt", 'w', encoding='utf-8') as f:
                            f.write(config_input.AI_PROMPT + "\n" + profile_header_text)

                        ai_response = await check_using_ai(config_input.AI_PROMPT, profile_header_text)
                        
                        print("AI RESPONSE","\n",ai_response)

                        if "false" in ai_response.lower():
                            pass
                        elif str(ai_response.lower().strip()) == "true":
                            row = await copy_profile(page=page)
                            update_excel(row)
            except Exception as e:
                print(f"Error processing profile header for {username}: {e}")
        except Exception as e:
            with open(settings.USERNAMES_FILE_PATH,'a') as f:
                f.write(username + "\n")
                print(username,"are saved")
                print(e)
            # print(f"Error visiting {url}: {e}")


async def every_profile_checker():
    browser, context = await get_browser_and_context()
    username_chunks = split_usernames_into_chunks()

    tasks = []
    for chunk in username_chunks:
        page = await context.new_page()
        tasks.append(check_profile_using_ai(page, chunk))

    await asyncio.gather(*tasks)


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

    # Websites
    websites = re.findall(r'(https?://[^\s]+|www\.[^\s]+)', complete_header_text)
    website_str = ", ".join([url.rstrip('.,') for url in websites])

    # all header section (remove contacts and websites from it if needed)
    all_info = complete_header_text.strip()

    # Final row in order of: Name, Username, Post Count, Followers, Following, Phone/Email, Website, Bio
    print([name, username, post_count, followers, following, contact_str, website_str, bio, all_info])
    return [name, username, post_count, followers, following, contact_str, website_str, bio, all_info]


async def clear_browser_cache(page):
    await page.goto("chrome://settings/clearBrowserData?search=cache")  # now await

    # Run pyautogui code in a separate thread to not block the async loop
    time.sleep(1)
    await asyncio.to_thread(pyautogui.press, 'tab')
    time.sleep(1)
    await asyncio.to_thread(pyautogui.press, 'enter')
    time.sleep(1)
    await asyncio.to_thread(pyautogui.hotkey, 'ctrl', 'w')

    

if __name__ == "__main__":
    try:
        asyncio.run(every_profile_checker())
    except Exception as e:
        print(f"Unhandled error: {e}")






