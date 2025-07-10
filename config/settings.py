import random

# Var where the leadership info would be store after ai processed
OUTPUT_FILE_PATH = "data/ouput/InstaLeaderShip.xlsx"


# Random sleep before every action
RANDOM_CLICK_SLEEP = random.randint(1,5)

#
SLEEP_BETWEEN_PAGE_LOADS = random.randint(3,6)*1000

# screenshot folder for debuging
SCREENSHOT_FOLDER = "data/screenshot"

# file where store usernames
USERNAMES_FILE_PATH = 'data/ouput/usernames.txt'

# Using default for CDP
REMOTE_DEBUGGING_PORT = "9222"  


# Those usernames which we have checked
CHECKED_USERNAMES_FILE_PATH = 'data/ouput/checked_usernames.txt'


# size of tabs that should be open for check every profiles header section
chunk_size = 5

# excel lead file path
LEADS_FILE_PATH = 'data/ouput/InstaLeaderShip.xlsx'

# ON/OFF HEADLESS MODE
HEADLESS = True

