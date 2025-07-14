import random

# Var where the leadership info would be store after ai processed
LEADS_FILE_PATH = "data/ouput/InstaLeaderShip.xlsx"

# Random sleep before every action
RANDOM_CLICK_SLEEP = random.randint(1,5)

#
SLEEP_BETWEEN_PAGE_LOADS = random.randint(5,10)

# screenshot folder for debuging
SCREENSHOT_FOLDER = r"data/screenshot"

# file where store usernames
USERNAMES_FILE_PATH = r'data/ouput/usernames.txt'

# proxies file path
PROXIES_FILE_PATH = r"data\input\proxies.txt"

VIDEOS_FOLDER_PATH = "videos"

# Those usernames which we have checked
CHECKED_USERNAMES_FILE_PATH = r'data/ouput/checked_usernames.txt'

# size of tabs that should be open for check every profiles header section
chunk_size = 4

# ON/OFF HEADLESS MODE
HEADLESS = True

# ON/OFF video from spider what they did and video are saving videos folder
record_video = "OFF"


#
wait_if_captcha_appear = 5*100