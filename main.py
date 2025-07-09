import asyncio
from core.scraper import open_and_scrape_followers, load_saved_usernames,prevent_display_off,enable_default_sleep_behavior
from core.browser import get_browser_and_context
from data.input import config_input
import pyautogui
from ai.extractor import every_profile_checker

async def followers_scraper_main():
    load_saved_usernames()
    browser, context = await get_browser_and_context()
    tasks = []

    for username in config_input.USERNAMES:
        page = await context.new_page()
        tasks.append(open_and_scrape_followers(page, username))

    await asyncio.gather(*tasks)

    
if __name__ == "__main__":
    try:
        prevent_display_off()
        # asyncio.run(followers_scrap)
        pyautogui.hotkey('ctrl','w')
        
        asyncio.run(every_profile_checker())
    except Exception as e:
        print(e)
    finally:
        enable_default_sleep_behavior()
        pyautogui.hotkey('ctrl','w')

