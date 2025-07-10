from dotenv import load_dotenv
import os
import time

# laod env
load_dotenv()

async def login_insta(context):
    page = await context.new_page()
    await page.goto("https://www.instagram.com/accounts/login/?hl=en")
    await page.locator("//input[@name='username']").wait_for()
    await page.locator("//input[@name='username']").fill(os.getenv("EMAIL"))
    await page.locator("//input[@name='password']").fill(os.getenv("PASS"))

    # click login btn
    await page.locator("//button[.='Log in']").click()

    # now wait unitl home page load sucessfully
    try:
        await page.wait_for_url("https://www.instagram.com/accounts/onetap/?next=%2F&hl=en", timeout=30000)
        print("✅ Login Sucessfully")
        time.sleep(4)
    except Exception as e:
        print("❌ Login Failed")
        print(e)
    await page.close()







