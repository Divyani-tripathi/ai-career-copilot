from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    models = client.models.list()
    print("Available models:\n")
    for m in models:
        print(m.name)
except Exception as e:
    print("ERROR:", e)