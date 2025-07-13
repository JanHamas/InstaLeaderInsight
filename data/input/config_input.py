AI_PROMPT = """ "
Only respond with a single word: `true` or `false`.
Definition:
Return `true` only if the profile clearly belongs to a *tech leadership individual* (e.g., CTO, VP of Engineering, Tech Founder, Head of Product, or Software Leader)..
If it does not meet this condition, return `false`.
Do not provide any explanation. Do not describe the profile. Return only one word: true or false.

Profile:
"""

USERNAMES = [
    "tech.unicorn", "thisistechtoday", "phoneridar", "techgiving",
    "allthingstori123", "klug_tech", "vanlifetech", "mastertechpk",
    "itstechnical8", "blackwomentalktech", "mobilopedia", "techikeee",
    "techinfluencemedia", "bigtechmoney", "tec_tok_by_hareesh", "imjustcyrus",
    "iJustine",
    # "andrewethanzeng", "betterscreentime", "meshaobbreona", "cleoabram",
    # "austinnasso", "taramreed_", "familytech", "alliekmiller",
    # "karlconrad", "lilmiquela", "lovee_charms", "hadyouatsalaam",
    # "tayllorlloyd", "tiffintech", "shudu.gram", "tatam.digital"
]




# how much followers or following want to extract per profile
user_connection = "following"
how_much_followers_check = 50000

# if you want to only scrap verified then write yes otherwise we are scraping all profiles
is_verified = "No"

# if below names appear in profile header section then we sent header all text to ai for matching further criteria
LEADERSHIP_KEYWORDS = [
    "CEO",
    "Founder",
    "Co-Founder",
    "Managing Partner",
    "Founding Partner",
    "Chairman",
    "Chairwoman",
    "Board Member",
    "President",
    "Vice President",
    "Executive Vice President",
    "Senior Vice President",
    "Associate Vice President",
    "COO",
    "CFO",
    "CTO",
    "CIO",
    "CMO",
    "CHRO",
    "CPO",
    "CSO",
    "CXO",
    "Head of Growth",
    "Head of Product",
    "Head of Engineering",
    "Technical Co-Founder",
    "Lead Developer",
    "Creative Director",
    "Art Director",
    "Content Director",
    "Brand Manager"
]

