from groq import Groq
import os,traceback
from dotenv import load_dotenv


#load
load_dotenv()

# this function are sending the user bio to ai for get TRUE/FALSE words base on provided criteria which in config_input.py
async def ai_profile_checker(ai_prompt: str, header_text: str) -> str | None:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    messages = [{"role": "user", "content": f"{ai_prompt}{header_text}"}]

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        response_text = completion.choices[0].message.content.strip()
        return response_text
    except Exception as e:
        print("\nError:", e)
        print(traceback.format_exc())
        return None
