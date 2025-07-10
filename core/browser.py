
















































# browser = await playwright.chromium.connect_over_cdp(
    #     f"http://127.0.0.1:{settings.REMOTE_DEBUGGING_PORT}"
    # )
# # get chrome path dynamice across all OS
# def get_chrome_path():
#     system=platform.system().lower()
#     if system=="windows":
#         return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
#     elif system=="linux":
#         return "/usr/bin/google-chrome"
#     elif system=="darwin":
#         return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
#     else:
#         raise Exception("Unsupported OS")

# def get_user_data_dir(folder_name="surmed",base_folder="browsers"):
#     """
#     Return the full path to the user data  directory for chrome based on the user's OS.

#     Defualt sturcture:
#     ~/Desktop/browsers/surmed
#     """
#     desktop_path=Path.home() / "Desktop"  
#     return desktop_path / base_folder / folder_name  


# CHROME_PATH=get_chrome_path()
# USER_DATA_DIR=get_user_data_dir()


# def start_chrome() -> None:
#     if not os.path.exists(CHROME_PATH):
#         print("[-] Chrome executable not found! Check the path.")
#         return False

#     try:
#         subprocess.Popen([
#                 CHROME_PATH,
#                 f"--remote-debugging-port={settings.REMOTE_DEBUGGING_PORT}",
#                 f"--user-data-dir={USER_DATA_DIR}",  # still required for CDP connection
#                 "--no-first-run",
#                 "--no-default-browser-check",
#                 "--disable-popup-blocking",
#                 "--disable-gpu",
#                 "--disable-http-cache",
#                 "--disable-application-cache",
#             ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         time.sleep(3)
#         print("[+] Chrome launched successfully!")
#         return True
#     except Exception as e:
#         print(f"[-] Error launching Chrome: {e}")
#         return False


