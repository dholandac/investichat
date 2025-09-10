from dotenv import load_dotenv
import os
from chatbot.chatbot_logic.gemini_api import GeminiAPI
from chatbot.chatbot_logic.chatbot_logic import Chatbot

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    gemini_api_instance = GeminiAPI(api_key=GEMINI_API_KEY)
    chatbot_instance = Chatbot(gemini_api=gemini_api_instance)

    # Exemplo de uso:
    user_query = "Qual a melhor forma de investir para iniciantes?"
    response = chatbot_instance.get_response(user_query)
    print(f"Chatbot: {response}")
else:
    print("GEMINI_API_KEY não configurada no .env")