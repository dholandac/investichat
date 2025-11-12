from .models import UserStockSelection
from django.views.decorators.http import require_POST
from django.shortcuts import render
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import os
from dotenv import load_dotenv
from .chatbot_logic.gemini_api import GeminiAPI
from .chatbot_logic.chatbot_logic import Chatbot
from .models import Conversation, Message

load_dotenv()

# Logger para depuração
logger = logging.getLogger(__name__)

# Função para buscar cotação com cache (60s)
def get_stock_quote_cached(symbol, api_key):
    """
    Busca cotação com cache de 60 segundos.
    O JavaScript atualiza a cada 30s, então teremos:
    - 0s: API call (1-2s)
    - 30s: Cache hit (50ms) 
    - 60s: Cache expirado, nova API call
    Economiza ~66% das chamadas à API!
    """
    cache_key = f'stock_quote_{symbol}'
    quote_data = cache.get(cache_key)
    
    if quote_data is None:
        # Cache miss - busca da API
        from .finnhub_client import FinnhubAPIClient
        finnhub = FinnhubAPIClient(api_key)
        quote = finnhub.get_global_quote(symbol)
        
        if quote:
            quote_data = {
                'symbol': quote.symbol,
                'current_price': quote.current_price,
                'change': quote.change,
                'change_percent': quote.change_percent,
                'latest_trading_day': quote.latest_trading_day,
            }
            # Armazena no cache por 60 segundos
            cache.set(cache_key, quote_data, timeout=60)
            logger.debug(f"Cache MISS para {symbol} - buscado da API")
        else:
            return None
    else:
        logger.debug(f"Cache HIT para {symbol} - retornado do cache")
    
    return quote_data

# Instância global do chatbot (pode ser melhorada com cache ou sessão)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    gemini_api_instance = GeminiAPI(api_key=GEMINI_API_KEY)
    chatbot_instance = Chatbot(gemini_api=gemini_api_instance)
else:
    chatbot_instance = None

# Bloqueia o acesso do usuário caso ele não esteja logado, o enviando de volta para a página de login
from usuarios.models import PerfilUsuario

@ensure_csrf_cookie
@login_required(login_url="/auth/login/")
def chatbot(request):
    user_profile, created = PerfilUsuario.objects.get_or_create(user=request.user)
    show_questionnaire = not user_profile.questionario_completo
    
    # Busca ou cria a conversa mais recente do usuário (COM PREFETCH!)
    conversation = Conversation.objects.filter(
        user=request.user
    ).prefetch_related('messages').order_by('-updated_at').first()
    
    if not conversation:
        conversation = Conversation.objects.create(user=request.user, title='Conversa atual')

    # Carrega últimas 50 mensagens (já foram carregadas com prefetch_related)
    messages = list(conversation.messages.all().order_by('created_at')[:50])
    
    # Busca cotações das ações selecionadas COM CACHE
    investment_quotes = []
    try:
        selection = UserStockSelection.objects.get(user=request.user)
        user_stocks = selection.get_stock_list()
        
        api_key = os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_KEY')
        
        if api_key and user_stocks:
            for symbol in user_stocks:
                try:
                    quote_data = get_stock_quote_cached(symbol, api_key)
                    if quote_data:
                        investment_quotes.append(quote_data)
                except Exception as e:
                    logger.warning(f"Erro ao buscar cotação para {symbol}: {e}")
    except UserStockSelection.DoesNotExist:
        pass

    # Busca notícias do mercado com cache (Marketaux - PT-BR)
    market_news = []
    try:
        marketaux_key = os.getenv('MARKETAUX_API_KEY')
        if marketaux_key:
            cache_key = 'market_news_marketaux'
            market_news = cache.get(cache_key)
            
            if market_news is None:
                from .marketaux_client import MarketauxClient
                marketaux = MarketauxClient(marketaux_key)
                # Busca notícias em português do Brasil sobre mercado financeiro
                market_news = marketaux.get_market_news(
                    languages='pt',
                    countries='br',
                    limit=9,
                    filter_entities=True
                )
                # Armazena no cache por 1 hora para economizar requisições
                cache.set(cache_key, market_news, timeout=3600)
                logger.debug("Cache MISS para notícias Marketaux - buscado da API")
            else:
                logger.debug("Cache HIT para notícias Marketaux - retornado do cache")
    except Exception as e:
        logger.warning(f"Erro ao buscar notícias do Marketaux: {e}")

    from datetime import datetime
    return render(request, 'chatbot/chatbot.html', {
        'show_questionnaire': show_questionnaire,
        'conversation_id': conversation.id,
        'history': messages,
        'investment_quotes': investment_quotes,
        'market_news': market_news,
        'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    })

# Rota para processar mensagens do usuário e retornar respostas do chatbot
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


            # --- CONTEXTO DINÂMICO PARA O CHATBOT ---
            # 1. Lista de ações disponíveis (do dropdown)
            all_stocks = [
                {"symbol": "AAPL", "name": "Apple"},
                {"symbol": "MSFT", "name": "Microsoft"},
                {"symbol": "TSLA", "name": "Tesla"},
                {"symbol": "GOOG", "name": "Alphabet"},
                {"symbol": "AMZN", "name": "Amazon"},
                {"symbol": "META", "name": "Meta"},
                {"symbol": "NFLX", "name": "Netflix"},
                {"symbol": "NVDA", "name": "Nvidia"},
                {"symbol": "BRK.B", "name": "Berkshire Hathaway"},
                {"symbol": "JPM", "name": "JPMorgan Chase"},
                {"symbol": "V", "name": "Visa"},
                {"symbol": "DIS", "name": "Disney"},
                {"symbol": "PYPL", "name": "PayPal"},
                {"symbol": "INTC", "name": "Intel"},
                {"symbol": "ADBE", "name": "Adobe"},
                {"symbol": "ORCL", "name": "Oracle"},
                {"symbol": "CSCO", "name": "Cisco"},
                {"symbol": "PEP", "name": "PepsiCo"},
                {"symbol": "KO", "name": "Coca-Cola"},
                {"symbol": "MCD", "name": "McDonald's"},
            ]

            # 2. Seleção do usuário (do banco)
            try:
                selection = UserStockSelection.objects.get(user=request.user)
                user_stocks = selection.get_stock_list()
            except UserStockSelection.DoesNotExist:
                user_stocks = []

            # 3. Resumo de mercado (variação das ações selecionadas)
            from .finnhub_client import FinnhubAPIClient
            market_info = None
            try:
                api_key = os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_KEY')
                if api_key and user_stocks:
                    finnhub = FinnhubAPIClient(api_key)
                    quotes = []
                    for symbol in user_stocks:
                        quote = finnhub.get_global_quote(symbol)
                        if quote:
                            quotes.append(quote)
                    if quotes:
                        market_info = "; ".join([
                            f"{q.symbol}: {q.current_price:.2f} ({q.change:+.2f}, {q.change_percent})" for q in quotes
                        ])
            except Exception as e:
                logger.warning(f"Erro ao obter market_info: {e}")

            # 3.5 Notícias do mercado (contexto adicional)
            market_news_context = None
            try:
                marketaux_key = os.getenv('MARKETAUX_API_KEY')
                if marketaux_key:
                    cache_key = 'market_news_marketaux'
                    market_news = cache.get(cache_key)
                    
                    if market_news is None:
                        from .marketaux_client import MarketauxClient
                        marketaux = MarketauxClient(marketaux_key)
                        market_news = marketaux.get_market_news(
                            languages='pt',
                            countries='br',
                            limit=9,
                            filter_entities=True
                        )
                        cache.set(cache_key, market_news, timeout=3600)
                    
                    if market_news:
                        # Formata notícias para contexto da IA
                        news_summaries = []
                        for news in market_news[:5]:  # Usa as 5 primeiras notícias
                            news_text = f"{news.get('headline', '')}"
                            if news.get('summary'):
                                news_text += f": {news.get('summary')}"
                            news_summaries.append(news_text)
                        market_news_context = " | ".join(news_summaries)
            except Exception as e:
                logger.warning(f"Erro ao obter notícias para contexto: {e}")

            # 4. Histórico recente
            recent_history = [
                { 'role': m.role, 'content': m.content }
                for m in conversation.messages.all().order_by('-created_at')[:12]
            ]
            recent_history.reverse()  # Garantir ordem cronológica do mais antigo ao mais recente
            logger.debug("chat_message history_count=%d conversation_id=%s", len(recent_history), conversation.id)

            # 5. Chamada do chatbot com contexto
            try:
                bot_response = chatbot_instance.get_response(
                    user_message,
                    perfil_investidor,
                    history=recent_history,
                    user_stocks=user_stocks,
                    all_stocks=all_stocks,
                    market_info=market_info,
                    market_news=market_news_context
                )
            except Exception as e:
                # Erro da API Gemini - retorna mensagem simplificada
                logger.error(f"Erro ao gerar resposta do chatbot: {e}")
                return JsonResponse({'error': str(e)}, status=503)

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

# Endpoint para salvar seleção de ações do usuário
@login_required(login_url="/auth/login/")
@require_POST
def save_stock_selection(request):
    try:
        logger.debug(f"save_stock_selection - Method: {request.method}, CSRF: {request.META.get('HTTP_X_CSRFTOKEN', 'NOT FOUND')}")
        data = json.loads(request.body)
        stocks = data.get('stocks', [])
        logger.debug(f"save_stock_selection - Stocks: {stocks}")
        if not isinstance(stocks, list):
            return JsonResponse({'error': 'Formato inválido'}, status=400)
        selection, _ = UserStockSelection.objects.get_or_create(user=request.user)
        selection.set_stock_list(stocks)
        logger.debug(f"save_stock_selection - Success")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"save_stock_selection - Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
# Endpoint para retornar seleção de ações salva do usuário
@login_required(login_url="/auth/login/")
def get_stock_selection(request):
    try:
        selection, _ = UserStockSelection.objects.get_or_create(user=request.user)
        return JsonResponse({'stocks': selection.get_stock_list()})
    except Exception as e:
        return JsonResponse({'stocks': [], 'error': str(e)}, status=500)


@login_required(login_url="/auth/login/")
def refresh_investment_panel(request):
    """
    View HTMX para atualizar o painel de investimentos sem recarregar a página
    Retorna apenas o HTML do painel de investimentos
    USA CACHE para economizar chamadas à API!
    """
    investment_quotes = []
    try:
        selection = UserStockSelection.objects.get(user=request.user)
        user_stocks = selection.get_stock_list()
        
        api_key = os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_KEY')
        
        if api_key and user_stocks:
            for symbol in user_stocks:
                try:
                    quote_data = get_stock_quote_cached(symbol, api_key)
                    if quote_data:
                        investment_quotes.append(quote_data)
                except Exception as e:
                    logger.warning(f"Erro ao buscar cotação para {symbol}: {e}")
    except UserStockSelection.DoesNotExist:
        # Se não houver seleção, usa valores padrão
        user_stocks = ['AAPL', 'MSFT', 'TSLA']
        api_key = os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_KEY')
        
        if api_key:
            for symbol in user_stocks:
                try:
                    quote_data = get_stock_quote_cached(symbol, api_key)
                    if quote_data:
                        investment_quotes.append(quote_data)
                except Exception as e:
                    logger.warning(f"Erro ao buscar cotação para {symbol}: {e}")
    
    # Se for requisição HTMX ou tiver o header HX-Request, retorna HTML
    if request.headers.get('HX-Request') or request.headers.get('Hx-Request'):
        from datetime import datetime
        return render(request, 'chatbot/_investment_quotes.html', {
            'investment_quotes': investment_quotes,
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        })
    
    # Senão retorna JSON (compatibilidade)
    return JsonResponse({
        'status': 'success',
        'investment_quotes': investment_quotes,
    })