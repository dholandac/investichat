from google import genai

class GeminiAPI:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_content(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Erro ao gerar conteúdo com Gemini API: {e}"


