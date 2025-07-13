from dotenv import load_dotenv
import os
from util.bypass_captcha import check_and_solve_captcha
from aioconsole import ainput

# Load environment variables
load_dotenv()

async def pause_for_user_input():
    await ainput("🔍 Check for CAPTCHA manually if needed. Press Enter to continue...")

async def login_insta(context):
    page = await context.new_page()
    await page.goto("https://www.instagram.com/accounts/login/", timeout=30000)

    # Check for alternate Instagram login format
    content = await page.content()
    if "See everyday moments from" in content:
        print("⚠️ The login page appeared in a different format.")
        await pause_for_user_input()


    # Fill in login credentials
    await page.locator("//input[@name='username']").wait_for()
    await page.locator("//input[@name='username']").fill(os.getenv("EMAIL"))
    await page.locator("//input[@name='password']").fill(os.getenv("PASS"))

    # Click login button
    await page.locator("//button[normalize-space()='Log in']").click()

    # Solve CAPTCHA if detected
    await check_and_solve_captcha(page)


