from .gemini_api import GeminiAPI

class Chatbot:
    def __init__(self, gemini_api: GeminiAPI):
        self.gemini_api = gemini_api
        self.conversation_history = []

    def get_response(self, user_message: str) -> str:
        # Adiciona a mensagem do usuário ao histórico
        self.add_to_history("user", user_message)

        # Constrói o prompt com base no histórico (opcional, dependendo da complexidade)
        # No momento, apenas a última mensagem do usuário é usada como prompt
        prompt = user_message

        # Gera a resposta usando a Gemini API
        bot_response = self.gemini_api.generate_content(prompt)

        # Adiciona a resposta do bot ao histórico
        self.add_to_history("bot", bot_response)

        return bot_response

    def add_to_history(self, role: str, message: str):
        self.conversation_history.append({"role": role, "message": message})

    def get_conversation_history(self):
        return self.conversation_history


