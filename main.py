import asyncio
from util.helpers import prevent_display_off,enable_default_sleep_behavior
from core.scraper import followers_lister_main
from scrape_profile.scrape_profles import every_profile_checker

if __name__ == "__main__":
    try:
        prevent_display_off()
        # asyncio.run(followers_lister_main())
        asyncio.run(every_profile_checker())
    except Exception as e:
        print(e)
    finally:
        enable_default_sleep_behavior()


