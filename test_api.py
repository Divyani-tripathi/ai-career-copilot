from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",   # ✅ FINAL FIX
        contents="Say hello in one sentence"
    )

    print("✅ API WORKING")
    print(response.text)

except Exception as e:
    print("❌ API ERROR:", e)