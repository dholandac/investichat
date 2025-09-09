from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=""
)
print(response.text)