import random

# 5 latest Windows Chrome user agents (Update Chrome version as needed)
user_agents = [
    # Windows 10 - Standard Desktop
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.188 Safari/537.36",

    # Windows 11
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.188 Safari/537.36",

    # Windows 10 with slightly different UA
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.100 Safari/537.36",

    # Windows 10 - Nvidia GeForce Now
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; NVIDIA) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.188 Safari/537.36",

    # Windows 10 - Edge (uses Chrome UA but looks slightly different)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.188 Safari/537.36 Edg/116.0.1938.69"
]

# Pick one randomly
random_user_agent = random.choice(user_agents)
