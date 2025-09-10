from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from dotenv import load_dotenv
from .chatbot_logic.gemini_api import GeminiAPI
from .chatbot_logic.chatbot_logic import Chatbot

load_dotenv()

# Instância global do chatbot (pode ser melhorada com cache ou sessão)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    gemini_api_instance = GeminiAPI(api_key=GEMINI_API_KEY)
    chatbot_instance = Chatbot(gemini_api=gemini_api_instance)
else:
    chatbot_instance = None

# Bloqueia o acesso do usuário caso ele não esteja logado, o enviando de volta para a página de login
@login_required(login_url="/auth/login/")
def chatbot(request):
    return render(request, 'chatbot/chatbot.html')

@csrf_exempt
@login_required(login_url="/auth/login/")
def chat_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            if not user_message:
                return JsonResponse({'error': 'Mensagem vazia'}, status=400)
            
            if not chatbot_instance:
                return JsonResponse({'error': 'Chatbot não configurado. Verifique a GEMINI_API_KEY'}, status=500)
            
            # Gera resposta usando o chatbot
            bot_response = chatbot_instance.get_response(user_message)
            
            return JsonResponse({
                'response': bot_response,
                'status': 'success'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

