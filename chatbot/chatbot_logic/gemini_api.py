from google import genai
import re

class GeminiAPI:
    # Inicializa o cliente Gemini com a chave da API e o modelo desejado
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def _simplify_error_message(self, error_str: str) -> str:
        """Simplifica mensagens de erro para exibição ao usuário"""
        error_lower = str(error_str).lower()
        
        # Erro 503 - Sobrecarga
        if '503' in error_str or 'overloaded' in error_lower:
            return "O serviço está temporariamente sobrecarregado. Tente novamente em alguns segundos."
        
        # Erro 429 - Rate limit
        if '429' in error_str or 'rate limit' in error_lower or 'quota' in error_lower:
            return "Limite de requisições atingido. Aguarde alguns minutos."
        
        # Erro 401/403 - Autenticação
        if '401' in error_str or '403' in error_str or 'unauthorized' in error_lower or 'forbidden' in error_lower:
            return "Erro de autenticação. Verifique a chave da API."
        
        # Erro de rede
        if 'connection' in error_lower or 'timeout' in error_lower or 'network' in error_lower:
            return "Erro de conexão. Verifique sua internet."
        
        # Extrai mensagem do erro se houver
        message_match = re.search(r"'message':\s*'([^']+)'", error_str)
        if message_match:
            return message_match.group(1)
        
        # Fallback genérico
        return "Erro ao processar sua mensagem. Tente novamente."

    # Gera conteúdo com base no prompt fornecido
    def generate_content(self, prompt: str) -> str:
        try:
            # Chama a API Gemini para gerar conteúdo
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            return response.text
        except Exception as e:
            # Retorna mensagem simplificada
            simplified_error = self._simplify_error_message(str(e))
            raise Exception(simplified_error)


