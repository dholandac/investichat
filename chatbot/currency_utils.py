"""
Utilitários para conversão de moedas
"""
from django.core.cache import cache
from .finnhub_client import FinnhubAPIClient
import os
from dotenv import load_dotenv

load_dotenv()


def get_api_key():
    """Obtém a chave da API do Finnhub"""
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        raise ValueError("FINNHUB_API_KEY não configurada")
    return api_key


def get_usd_to_brl_rate():
    """Obtém a taxa de câmbio USD para BRL com cache"""
    cache_key = 'usd_brl_rate'
    rate = cache.get(cache_key)
    
    if rate is None:
        try:
            api_key = get_api_key()
            client = FinnhubAPIClient(api_key)
            # Tenta obter cotação do par USD/BRL
            quote = client.get_global_quote('USDBRL=X')
            if quote and quote.current_price > 0:
                rate = quote.current_price
                # Cache por 1 hora (taxa de câmbio não muda muito rápido)
                cache.set(cache_key, rate, timeout=3600)
            else:
                # Fallback: usa taxa fixa se API não retornar
                rate = 5.20  # Taxa aproximada
                cache.set(cache_key, rate, timeout=3600)
        except Exception as e:
            # Em caso de erro, usa taxa fixa
            print(f"Erro ao obter taxa de câmbio: {e}")
            rate = 5.20
            cache.set(cache_key, rate, timeout=3600)
    
    return rate


def convert_usd_to_brl(usd_value):
    """Converte valor de USD para BRL"""
    rate = get_usd_to_brl_rate()
    return usd_value * rate

