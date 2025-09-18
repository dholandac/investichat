from django.shortcuts import render
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from dotenv import load_dotenv
from .chatbot_logic.gemini_api import GeminiAPI
from .chatbot_logic.chatbot_logic import Chatbot
from .models import Conversation, Message

load_dotenv()

# Logger para depuração
logger = logging.getLogger(__name__)

# Instância global do chatbot (pode ser melhorada com cache ou sessão)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    gemini_api_instance = GeminiAPI(api_key=GEMINI_API_KEY)
    chatbot_instance = Chatbot(gemini_api=gemini_api_instance)
else:
    chatbot_instance = None

# Bloqueia o acesso do usuário caso ele não esteja logado, o enviando de volta para a página de login
from usuarios.models import PerfilUsuario

@login_required(login_url="/auth/login/")
def chatbot(request):
    user_profile, created = PerfilUsuario.objects.get_or_create(user=request.user)
    show_questionnaire = not user_profile.questionario_completo
    # Busca ou cria a conversa mais recente do usuário
    conversation = Conversation.objects.filter(user=request.user).order_by('-updated_at').first()
    if not conversation:
        conversation = Conversation.objects.create(user=request.user, title='Conversa atual')

    # Carrega últimas 50 mensagens para exibir no template
    messages = list(conversation.messages.all().order_by('created_at')[:50])

    return render(request, 'chatbot/chatbot.html', {
        'show_questionnaire': show_questionnaire,
        'conversation_id': conversation.id,
        'history': messages,
    })

# Rota para processar mensagens do usuário e retornar respostas do chatbot
@csrf_exempt
@login_required(login_url="/auth/login/")
def chat_message(request):
    if request.method == 'POST':
        try:
            # Lê a mensagem do corpo da requisição
            data = json.loads(request.body)
            user_message = data.get('message', '')
            conversation_id = data.get('conversation_id')
            
            # Valida a mensagem
            if not user_message:
                return JsonResponse({'error': 'Mensagem vazia'}, status=400)
            
            # Verifica se o chatbot está configurado corretamente
            if not chatbot_instance:
                return JsonResponse({'error': 'Chatbot não configurado. Verifique a chave da API'}, status=500)

            # Localiza conversa existente ou cria nova
            conversation = None
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user)
                except Conversation.DoesNotExist:
                    conversation = None
            if not conversation:
                conversation = Conversation.objects.create(user=request.user, title='Conversa atual')

            # Persiste a mensagem do usuário
            Message.objects.create(conversation=conversation, role='user', content=user_message)

            # Busca perfil do usuário
            try:
                user_profile = PerfilUsuario.objects.get(user=request.user)
                perfil_investidor = user_profile.perfil_investidor
            except PerfilUsuario.DoesNotExist:
                perfil_investidor = None
            # Loga o perfil atual para depuração
            logger.debug("chat_message perfil_investidor=%s user=%s", perfil_investidor, request.user.username)

            # Gera resposta usando o chatbot, passando o perfil e histórico recente da conversa
            recent_history = [
                { 'role': m.role, 'content': m.content }
                for m in conversation.messages.all().order_by('-created_at')[:12]
            ]
            recent_history.reverse()  # Garantir ordem cronológica do mais antigo ao mais recente
            logger.debug("chat_message history_count=%d conversation_id=%s", len(recent_history), conversation.id)

            bot_response = chatbot_instance.get_response(
                user_message,
                perfil_investidor,
                history=recent_history
            )

            # Persiste a resposta do bot
            Message.objects.create(conversation=conversation, role='bot', content=bot_response)
            conversation.save()  # atualiza updated_at
            
            # Retorna a resposta como JSON
            return JsonResponse({
                'response': bot_response,
                'conversation_id': conversation.id,
                'status': 'success'
            })
        
        # Tratamento de erros
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)
