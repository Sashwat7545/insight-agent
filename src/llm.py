import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL")  # optional

RETRYABLE = (429, 500, 503, 504)


def generate(contents, max_retries=4):
    models = [MODEL] + ([FALLBACK_MODEL] if FALLBACK_MODEL else [])
    last_error = None

    for model in models:
        delay = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model, contents=contents
                )
                return response.text
            except errors.APIError as e:
                last_error = e
                if e.code not in RETRYABLE:
                    raise  # 404, 401 jaise errors retry se theek nahi hote
                print(f"[{model}] error {e.code}, retry {attempt + 1} in {delay}s")
                time.sleep(delay)
                delay *= 2  # 2s, 4s, 8s, 16s
    raise last_error