from urllib.parse import urlparse, parse_qs
from twocaptcha import TwoCaptcha
from dotenv import load_dotenv
from util.helper import get_latest_instagram_otp
import os

# Load .env variables
load_dotenv()

# Solve CAPTCHA using 2Captcha
def solve_recaptcha_v2(sitekey, url):
    print("[*] Solving CAPTCHA using 2Captcha...")
    solver = TwoCaptcha(apiKey=os.getenv("CAPTCHA_API_KEY"))
    try:
        result = solver.recaptcha(sitekey=sitekey, url=url)
        print("✅ CAPTCHA Solved:", result)
        return result["code"]
    except Exception as e:
        print(f"❌ CAPTCHA solving failed: {e}")
        return None

# Extract sitekey dynamically from the page
async def get_site_key(page):
    try:
        # Method 1: Check div.g-recaptcha data-sitekey attribute
        recaptcha_div = await page.query_selector('div.g-recaptcha[data-sitekey]')
        if recaptcha_div:
            sitekey = await recaptcha_div.get_attribute("data-sitekey")
            if sitekey:
                print(f"✅ Found sitekey (div): {sitekey}")
                return sitekey

        # Method 2: Check reCAPTCHA iframe src parameter
        iframe = await page.query_selector('iframe[src*="/recaptcha/api2"][src*="k="]')
        if iframe:
            iframe_src = await iframe.get_attribute("src")
            parsed = urlparse(iframe_src)
            query = parse_qs(parsed.query)
            sitekey = query.get("k", [None])[0]
            if sitekey:
                print(f"✅ Found sitekey (iframe): {sitekey}")
                return sitekey

        # Method 3: Check script src URL
        script = await page.query_selector('script[src*="/recaptcha/api.js"]')
        if script:
            script_src = await script.get_attribute("src")
            parsed = urlparse(script_src)
            query = parse_qs(parsed.query)
            sitekey = query.get("k", [None])[0]
            if sitekey:
                print(f"✅ Found sitekey (script): {sitekey}")
                return sitekey

        print("⚠️ Sitekey not found through any method")
        return None
    except Exception as e:
        print(f"❌ Error extracting sitekey: {e}")
        return None



# Check and solve CAPTCHA if present
async def check_and_solve_captcha(page):
    try:
        # Wait for potential CAPTCHA elements to load
        await page.wait_for_timeout(7000)
        
        # Detect CAPTCHA presence
        # if await page.locator("iframe[src*='recaptcha'], div.g-recaptcha").count() > 0:
        if "challenge/" in page.url:
            print("⚠️ CAPTCHA detected!")
            sitekey = await get_site_key(page)
            if sitekey:
                token = solve_recaptcha_v2(sitekey, page.url)
                if token:
                    # Inject the token into the page
                    await page.evaluate("""(token) => {
                        const responseEl = document.querySelector('[name="g-recaptcha-response"]');
                        if (responseEl) {
                            responseEl.value = token;
                        }
                    }""", token)
                    print("✅ CAPTCHA token injected.")
                else:
                    print("❌ Failed to solve CAPTCHA.")
            else:
                print("❌ No sitekey found.")
        else:
            # print("✅ No CAPTCHA found.")
            pass

        # Sometimes Instagram requires OTP verification
        if "auth_platform/" in page.url:
            print("🔐 Waiting for Instagram OTP from Gmail inbox...")
            otp = await get_latest_instagram_otp(os.getenv("EMAIL"), os.getenv("APP_PASSWORD"))
            if not otp:
                raise RuntimeError("❌ OTP not found—login will fail.")
            
            try:
                otp_input = page.locator('input[name="email"]')
                await otp_input.fill(otp)
                await otp_input.press("Enter")

                await page.wait_for_url(lambda u: "auth_platform/" not in u, timeout=30000)
                print("✅ OTP accepted, continuing with login.")
            except Exception as e:
                print(f"❌ OTP submission error: {e}")
                raise

            try:
                await page.wait_for_timeout(15000)
                print("✅ Login Successful")
                await page.close()
            except Exception as e:
                print("❌ Login Failed")
                raise

    except Exception as e:
        print(f"❌ Error in CAPTCHA check: {e}")
        raise