from config import settings
from data.input import config_input
from util.bypass_captcha import check_and_solve_captcha
from ai.ai_checker import ai_profile_checker
from util.helpers import (
    append_username,
    remove_username,
    resave_username,
    update_excel,
    copy_profile,
    split_usernames_into_chunks,
    load_proxies,
    humanize_behave_on_page
)
import random,gc
from playwright.async_api import Browser, async_playwright

async def create_context_with_proxy(browser: Browser, proxy: dict, use_storage: bool = True):
    try:        
        context_options = {
            # "proxy": proxy,
            # "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "viewport": {"width": 800, "height": 900},
        }
        if use_storage:
            context_options["storage_state"] = "auth.json"

        if settings.record_video.lower().strip() == "on":
            context_options["record_video_dir"] = "videos"
            context_options["record_video_size"] = {"width": 1280, "height": 720}

        context = await browser.new_context(**context_options)
        print(f"✅ Context created with proxy: {proxy['server']}")
        return context
    except Exception as e:
        print(f"❌ Failed to create context with proxy {proxy['server']} — {e}")
        return None

async def scrap_profile(browser: Browser, usernames: list[str]) -> None:
    proxies = load_proxies(settings.PROXIES_FILE_PATH)
    if not proxies:
        print("🚫 No proxies loaded. Exiting.")
        return

    random.shuffle(proxies)
    proxy = random.choice(proxies)
    context = await create_context_with_proxy(browser, proxy)

    for i, username in enumerate(usernames):
        if i > 0 and i % 20 == 0:
            # clean garbag collector
            gc.collect()
            if context:
                await context.close()
            proxy = random.choice(proxies)
            context = await create_context_with_proxy(browser, proxy)

        try:
            page = await context.new_page()
            
            url = f"https://www.{username}/"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

            await check_and_solve_captcha(page)

            header = page.locator("header, .header, div[role='banner']").first
            profile_header_text = (await header.inner_text()).lower()

            if not profile_header_text:
                await resave_username(username)
                continue

            await append_username(username)
            await remove_username(username)

            should_check = any(
                keyword.lower() in profile_header_text for keyword in config_input.LEADERSHIP_KEYWORDS
            )

            if not should_check:
                continue

            if config_input.is_verified.lower().strip() == "yes":
                verified_ele = page.locator("svg[aria-label='Verified']")
                if await verified_ele.count() == 0:
                    print("❌ Not Verified")
                    continue

            try:
                ai_response = await ai_profile_checker(config_input.AI_PROMPT, profile_header_text)
                print(f"🤖 AI RESPONSE: {ai_response}")
            except Exception as e:
                print(e)
                continue

            if ai_response.lower().strip() == "true":
                row = await copy_profile(page)
                update_excel(row)
            
            humanize_behave_on_page(page)

        except Exception as e:
            await resave_username(username)
        finally:
            if page:
                try:
                    if len(context.pages) > 1:
                        await page.close()
                except Exception as e:
                    print(f"⚠️ Page close error: {e}")


async def every_profile_checker():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=settings.HEADLESS)

    # await save_login_session(browser)  # Save auth.json once

    username_chunks = split_usernames_into_chunks()

    for chunk in username_chunks:
        await scrap_profile(browser, chunk)

    await browser.close()
    await p.stop()
