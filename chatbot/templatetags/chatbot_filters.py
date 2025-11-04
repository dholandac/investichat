from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='format_price')
def format_price(value):
    """Formata o preço em formato brasileiro"""
    try:
        price = float(value)
        return f"{price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return value


@register.filter(name='format_change')
def format_change(change, change_percent):
    """Formata a variação de preço com classe CSS apropriada"""
    try:
        change_value = float(change)
        is_positive = change_value >= 0
        css_class = 'positive' if is_positive else 'negative'
        symbol = '+' if is_positive else ''
        
        formatted_change = f"{change_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        return f'<span class="price-change {css_class}">{symbol}{formatted_change} ({change_percent})</span>'
    except (ValueError, TypeError):
        return ''


@register.filter(name='get_symbol_name')
def get_symbol_name(symbol):
    """Retorna o nome amigável do símbolo de ação"""
    symbol_names = {
        'AAPL': 'Apple',
        'MSFT': 'Microsoft',
        'TSLA': 'Tesla',
        'GOOG': 'Alphabet',
        'AMZN': 'Amazon',
        'META': 'Meta',
        'NFLX': 'Netflix',
        'NVDA': 'Nvidia',
        'BRK.B': 'Berkshire Hathaway',
        'JPM': 'JPMorgan Chase',
        'V': 'Visa',
        'DIS': 'Disney',
        'PYPL': 'PayPal',
        'INTC': 'Intel',
        'ADBE': 'Adobe',
        'ORCL': 'Oracle',
        'CSCO': 'Cisco',
        'PEP': 'PepsiCo',
        'KO': 'Coca-Cola',
        'MCD': "McDonald's",
        'PETR4.SA': 'Petrobras (PETR4)',
        'VALE3.SA': 'Vale (VALE3)',
        'ITUB4.SA': 'Itaú (ITUB4)',
        'BBDC4.SA': 'Bradesco (BBDC4)',
        '^BVSP': 'Ibovespa',
        'USDBRL=X': 'Dólar/Real',
        'BTC-USD': 'Bitcoin',
        '^GSPC': 'S&P 500'
    }
    return symbol_names.get(symbol, symbol)
