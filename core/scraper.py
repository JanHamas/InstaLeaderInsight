from config import settings
import os
import random
from data.input import config_input
import ctypes
import asyncio
import asyncio
from data.input import config_input
# from ai.extractor import every_profile_checker
from config.login import login_insta
from playwright.async_api import async_playwright
import random

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

# load those usernames which we have checked there profile and also those which we are saved in usernames.txt for checking there profile
saved_usernames = set()
async def load_saved_usernames():
    """Load usernames from usernames.txt file to prevent duplicates"""
    if os.path.exists(settings.USERNAMES_FILE_PATH):
        with open(settings.USERNAMES_FILE_PATH, 'r') as f:
            saved_usernames.update(line.strip() for line in f if line.strip())
    
    """Load usernames from checked_usernames.txt file to prevent duplicates"""
    if os.path.exists(settings.CHECKED_USERNAMES_FILE_PATH):
        with open(settings.CHECKED_USERNAMES_FILE_PATH, 'r') as f:
            saved_usernames.update(line.strip() for line in f if line.strip())
    
    GARBAG_URSERNAMES = [
    "instagram.com/Home",
    "instagram.com/Search",
    "instagram.com/Explore",
    "instagram.com/Reels",
    "instagram.com/Messages",
    "instagram.com/Notifications",
    "instagram.com/Create",
    "instagram.com/Profile",
    "instagram.com/More",
    "instagram.com/Also from Meta",
    ]
    saved_usernames.update(GARBAG_URSERNAMES)

# save new usernames without duplicate
async def save_new_usernames(follower_elements):
    global how_much_followers_check  # 👈 this tells Python to use the global variable
    with open(settings.USERNAMES_FILE_PATH, 'a') as f:
        for follower in follower_elements:
            try:
                user = await follower.inner_text()
                username = f"instagram.com/{user}"
                if username and username not in saved_usernames:
                    f.write(username + "\n")
                    saved_usernames.add(username)
                    how_much_followers_check += 1
                    print(username)
            except Exception as e:
                print(f"[!] Error reading user: {e}")

# for fast scrolling function we have defined
async def fast_scroll(page):
    for _ in range(6):
        await page.mouse.wheel(0, random.randint(800, 1200))  # Larger scroll
        await asyncio.sleep(random.uniform(0.3, 0.5))  # Smaller delay


# var that count followers/following to base on provided number from input.py files
how_much_followers_check = 0

# main func that opening users profiles and extract there followers/following
async def open_and_scrape_followers(page, username):
    """Scrape followers from an Instagram profile using a page with cache disabled."""
    # Navigate to the Instagram profile
    await page.goto(f"https://www.instagram.com/{username}/", timeout=120000, wait_until="load")

    # Random delay to mimic human behavior
    await asyncio.sleep(settings.SLEEP_BETWEEN_PAGE_LOADS)

    try:
        await page.locator(f"text='{config_input.user_connection}'").first.click()
        await page.wait_for_timeout(settings.RANDOM_CLICK_SLEEP)

        previous_usernames = set()
        unchanged_count = 0

        while True:
            followers = page.locator('a[role="link"][tabindex="0"] div div span[dir="auto"]')
            follower_elements = await followers.all()

            await save_new_usernames(follower_elements)

            current_usernames = set()
            for el in follower_elements:
                text = await el.inner_text()
                current_usernames.add(text.strip())

            if current_usernames == previous_usernames:
                unchanged_count += 1
            else:
                unchanged_count = 0

            if unchanged_count >= 2:
                print(f"✅ Reached bottom of the followers list for {username}")
                await page.close()
                break

            previous_usernames = current_usernames

            if how_much_followers_check >= config_input.how_much_followers_check:
                print(f"We have successfully extracted {how_much_followers_check} followers/folloing")
                await page.close()
                break

            
            scrollable = page.locator('div[style*="overflow"][style*="auto"]')
            await scrollable.wait_for(state="visible")
            await scrollable.scroll_into_view_if_needed()
            await scrollable.hover()
            await scrollable.focus()

            for _ in range(12):
                await fast_scroll(page=page)
            

    except Exception as e:
        print(f"[X] Error scraping {username}: {e}")
    finally:
        await page.close()
        


# for listing following/followers from provided usernames
async def followers_scraper_main():
    p = await async_playwright().start()
    await load_saved_usernames()

    browser = await p.chromium.launch(headless=settings.HEADLESS)
    context = await browser.new_context()
    
    # first login in insta
    await login_insta(context)

    tasks = []
    for username in config_input.USERNAMES:
        page = await context.new_page()
        tasks.append(open_and_scrape_followers(page, username))

    await asyncio.gather(*tasks)
