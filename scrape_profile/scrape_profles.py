from config import settings
from data.input import config_input
from util.bypass_captcha import check_and_solve_captcha
from ai.ai_checker import ai_profile_checker
from util import helpers
import asyncio
import random,os,gc
from playwright.async_api import Browser, async_playwright

async def create_context_with_proxy(browser: Browser, proxy: dict, use_storage: bool = True):
    try:        
        context_options = {
            "viewport": {"width": 800, "height": 900},
        }
        # list of login session
        list_of_accounts = [
            # "accounts\\auth0.json",
            "accounts\\auth1.json"
        ]
        
        if use_storage:
            context_options["storage_state"] = random.choice(list_of_accounts)

        if settings.record_video.lower().strip() == "on":
            context_options["record_video_dir"] = "videos"
            context_options["record_video_size"] = {"width": 1280, "height": 720}

        context = await browser.new_context(**context_options)
        print(f"✅ Context created with proxy: {proxy['server']}")
        return context
    except Exception as e:
        print(f"❌ Failed to create context with proxy {proxy['server']} — {e}")
        return None

def remove_usernames_from_file(usernames_to_remove: list[str]):
    try:
        if not os.path.exists(settings.USERNAMES_FILE_PATH):
            return
        with open(settings.USERNAMES_FILE_PATH, 'r', encoding='utf-8') as f:
            all_usernames = set(line.strip() for line in f if line.strip())
        remaining = all_usernames - set(usernames_to_remove)
        with open(settings.USERNAMES_FILE_PATH, 'w', encoding='utf-8') as f:
            for name in remaining:
                f.write(name + '\n')
    except Exception as e:
        print(f"⚠️ Error removing usernames: {e}")

async def scrap_profile(browser: Browser, usernames: list[str]) -> None:
    proxies = helpers.load_proxies(settings.PROXIES_FILE_PATH)
    if not proxies:
        print("🚫 No proxies loaded. Exiting.")
        return

    random.shuffle(proxies)

    # Load previously checked usernames
    checked_usernames = set()
    if os.path.exists(settings.CHECKED_USERNAMES_FILE_PATH):
        with open(settings.CHECKED_USERNAMES_FILE_PATH, 'r', encoding='utf-8') as f:
            checked_usernames = set(line.strip() for line in f if line.strip())

    usernames = [u.strip() for u in usernames if u.strip() and u.strip() not in checked_usernames]

    context = None
    proxy = random.choice(proxies)

    newly_checked_usernames = []
    failed_usernames = []

    for i, username in enumerate(usernames):
        # Rotate context and flush checked usernames every 30 profiles
        if i % 30 == 0:
            if context:
                await context.close()
                gc.collect()
            proxy = random.choice(proxies)
            context = await create_context_with_proxy(browser, proxy)

            # Write and remove batch checked usernames
            if newly_checked_usernames:
                with open(settings.CHECKED_USERNAMES_FILE_PATH, 'a', encoding='utf-8') as f:
                    for name in newly_checked_usernames:
                        f.write(name + '\n')
                remove_usernames_from_file(newly_checked_usernames)
                newly_checked_usernames.clear()

        try:
            page = await context.new_page()
            url = f"https://www.{username}/"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

            await asyncio.sleep((random.randint(1,4)))

            await check_and_solve_captcha(page)
            await helpers.humanize_behave_on_page(page)
            newly_checked_usernames.append(username)

            # if this error accure then we have to change insta account
            if "There's an issue and the page could not be loaded." in await page.content():
                print("There's an issue and the page could not be loaded.")
                await context.close()
                context = await create_context_with_proxy(browser, proxy)
                page = await context.new_page()

            header = page.locator("header, .header, div[role='banner']").first
            profile_header_text = (await header.inner_text()).lower()

            if not profile_header_text:
                failed_usernames.append(username)
                continue

            should_check = any(
                keyword.lower() in profile_header_text for keyword in config_input.LEADERSHIP_KEYWORDS
            )

            if not should_check:
                newly_checked_usernames.append(username)
                continue

            if config_input.is_verified.lower().strip() == "yes":
                verified_ele = page.locator("svg[aria-label='Verified']")
                if await verified_ele.count() == 0:
                    print("❌ Not Verified")
                    newly_checked_usernames.append(username)
                    continue

            try:
                ai_response = await ai_profile_checker(config_input.AI_PROMPT, profile_header_text)
                print(f"🤖 AI RESPONSE: {ai_response} for {username}")
            except Exception as e:
                print(e)
                failed_usernames.append(username)
                continue

            if ai_response.lower().strip() == "true":
                row = await helpers.copy_profile(page)
                await helpers.update_excel(row)


        except Exception as e:
            print(f"⚠️ Error scraping {username}: {e}")
            failed_usernames.append(username)
        finally:
            try:
                if len(context.pages) > 1:
                    await page.close()
            except Exception as e:
                print(f"⚠️ Page close error: {e}")

    # Final write of remaining usernames after loop
    if newly_checked_usernames:
        with open(settings.CHECKED_USERNAMES_FILE_PATH, 'a', encoding='utf-8') as f:
            for name in newly_checked_usernames:
                f.write(name + '\n')
        newly_checked_usernames.clear()
        remove_usernames_from_file(newly_checked_usernames)

    # Overwrite usernames.txt with failed only
    if failed_usernames:
        with open(settings.USERNAMES_FILE_PATH, 'a', encoding='utf-8') as f:
            for name in failed_usernames:
                f.write(name + '\n')
        failed_usernames.clear()

async def every_profile_checker():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=settings.HEADLESS)

    # await save_login_session(browser)  # Save auth.json once

    username_chunks = helpers.split_usernames_into_chunks()

    tasks = []
    for chunk in username_chunks:
        tasks.append(scrap_profile(browser, chunk))

    await asyncio.gather(*tasks)
    await browser.close()
    await p.stop()
