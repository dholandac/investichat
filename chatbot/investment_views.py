"""
Views para lidar com dados de investimento usando a API do Finnhub.
"""

import os
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .finnhub_client import FinnhubAPIClient


def get_api_key():
    """
    Obtém a chave da API do Finnhub das variáveis de ambiente.
    Para demonstração, usa uma chave limitada se não estiver configurada.
    """
    # Tenta obter a chave das variáveis de ambiente
    api_key = os.getenv('FINNHUB_API_KEY')
    
    # Se não encontrar, usa a chave demo (limitada)
    if not api_key:
        # Aviso: token público de demonstração do Finnhub não existe como no Alpha Vantage.
        # Deixar vazio resultará em erro 401. Para evitar quebra total em dev,
        # retornamos uma string placeholder que o backend vai tentar usar e logar erro; 
        # oriente configurar FINNHUB_API_KEY no .env.
        api_key = 'YOUR_FINNHUB_TOKEN_HERE'
    
    return api_key


@require_http_methods(["GET"])
def get_investment_data(request):
    """
    View para obter dados de investimento em tempo real.
    
    Returns:
        JsonResponse com dados de investimento formatados
    """
    try:
        api_key = get_api_key()
        client = FinnhubAPIClient(api_key)
        
        # Lista de ativos relevantes para brasileiros
        symbols = [
            # Observação: alguns símbolos locais podem exigir planos/feeds específicos no Finnhub.
            # Mantemos alguns globais com boa chance de cobertura.
            'AAPL',      # Apple (NASDAQ)
            'MSFT',      # Microsoft (NASDAQ)
            # 'BTC-USD',   # Bitcoin (removido por enquanto)
            'TSLA',      # Tesla
            # Você pode reintroduzir PETR4.SA/VALE3.SA/ITUB4.SA/BBDC4.SA caso seu token tenha cobertura B3
            # 'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA'
        ]
        
        investment_data = {
            'quotes': [],
            'last_updated': None
        }
        
        # Obtém cotações dos ativos principais
        for symbol in symbols[:4]:  # Limita para evitar exceder o limite da API
            quote = client.get_global_quote(symbol)
            if quote:
                investment_data['quotes'].append(quote.to_dict())
        
        # Removido: não calculamos mais maiores altas/baixas (market_summary)
        
        # Adiciona timestamp
        from datetime import datetime
        investment_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return JsonResponse({
            'status': 'success',
            'data': investment_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao obter dados de investimento: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_stock_quote(request, symbol):
    """
    View para obter cotação de um ativo específico.
    
    Args:
        symbol: Símbolo do ativo
        
    Returns:
        JsonResponse com dados da cotação
    """
    try:
        api_key = get_api_key()
        client = FinnhubAPIClient(api_key)
        
        quote = client.get_global_quote(symbol)
        
        if quote:
            return JsonResponse({
                'status': 'success',
                'data': quote.to_dict()
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Cotação não encontrada para o símbolo: {symbol}'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao obter cotação: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_time_series(request, symbol):
    """
    View para obter dados de série temporal de um ativo.
    
    Args:
        symbol: Símbolo do ativo
        
    Returns:
        JsonResponse com dados da série temporal
    """
    try:
        api_key = get_api_key()
        client = FinnhubAPIClient(api_key)
        
        interval = request.GET.get('interval', '5min')
        time_series = client.get_time_series_intraday(symbol, interval)
        
        # Converte para lista de dicionários
        time_series_data = [ts.to_dict() for ts in time_series]
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'symbol': symbol,
                'interval': interval,
                'time_series': time_series_data
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao obter série temporal: {str(e)}'
        }, status=500)


def chatbot_with_investment(request):
    """
    View principal que renderiza o template do chatbot com dados de investimento.
    """
    try:
        # Obtém dados iniciais de investimento para renderizar no template
        api_key = get_api_key()
        client = FinnhubAPIClient(api_key)
        
        # Dados básicos para exibição inicial
        initial_data = {
            'ibovespa': None,
            'dollar_rate': None,
            'bitcoin': None
        }
        
        # Tenta obter alguns dados básicos (sem bloquear se falhar)
        try:
            ibov_quote = client.get_global_quote('^BVSP')
            if ibov_quote:
                initial_data['ibovespa'] = ibov_quote.to_dict()
        except:
            pass
        
        try:
            dollar_quote = client.get_global_quote('USDBRL=X')
            if dollar_quote:
                initial_data['dollar_rate'] = dollar_quote.to_dict()
        except:
            pass
        
        context = {
            'initial_investment_data': initial_data
        }
        
        return render(request, 'chatbot/chatbot.html', context)
        
    except Exception as e:
        # Se houver erro, renderiza sem dados iniciais
        print(f"Erro ao obter dados iniciais: {str(e)}")
        return render(request, 'chatbot/chatbot.html', {'initial_investment_data': {}})

