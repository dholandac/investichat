from django import template
from chatbot.forms import StockSelectionForm
from chatbot.models import UserStockSelection

register = template.Library()


@register.inclusion_tag('chatbot/_stock_dropdown.html', takes_context=True)
def stock_dropdown(context):
    """
    Renderiza o dropdown de seleção de ações
    Usage: {% stock_dropdown %}
    """
    request = context.get('request')
    
    # Obtém as ações selecionadas do usuário
    selected_stocks = []
    if request and request.user.is_authenticated:
        try:
            selection = UserStockSelection.objects.get(user=request.user)
            selected_stocks = selection.get_stock_list()
        except UserStockSelection.DoesNotExist:
            selected_stocks = ['AAPL', 'MSFT', 'TSLA']  # Padrão
    
    # Lista de todas as ações disponíveis
    all_stocks = [
        {'value': 'AAPL', 'name': 'Apple (AAPL)'},
        {'value': 'MSFT', 'name': 'Microsoft (MSFT)'},
        {'value': 'TSLA', 'name': 'Tesla (TSLA)'},
        {'value': 'GOOG', 'name': 'Alphabet (GOOG)'},
        {'value': 'AMZN', 'name': 'Amazon (AMZN)'},
        {'value': 'META', 'name': 'Meta (META)'},
        {'value': 'NFLX', 'name': 'Netflix (NFLX)'},
        {'value': 'NVDA', 'name': 'Nvidia (NVDA)'},
        {'value': 'BRK.B', 'name': 'Berkshire Hathaway (BRK.B)'},
        {'value': 'JPM', 'name': 'JPMorgan Chase (JPM)'},
        {'value': 'V', 'name': 'Visa (V)'},
        {'value': 'DIS', 'name': 'Disney (DIS)'},
        {'value': 'PYPL', 'name': 'PayPal (PYPL)'},
        {'value': 'INTC', 'name': 'Intel (INTC)'},
        {'value': 'ADBE', 'name': 'Adobe (ADBE)'},
        {'value': 'ORCL', 'name': 'Oracle (ORCL)'},
        {'value': 'CSCO', 'name': 'Cisco (CSCO)'},
        {'value': 'PEP', 'name': 'PepsiCo (PEP)'},
        {'value': 'KO', 'name': 'Coca-Cola (KO)'},
        {'value': 'MCD', 'name': "McDonald's (MCD)"},
    ]
    
    return {
        'all_stocks': all_stocks,
        'selected_stocks': selected_stocks,
    }


@register.inclusion_tag('chatbot/_investment_panel.html', takes_context=True)
def investment_panel(context):
    """
    Renderiza o painel lateral de investimentos com cotações
    Usage: {% investment_panel %}
    """
    investment_quotes = context.get('investment_quotes', [])
    
    return {
        'investment_quotes': investment_quotes,
    }


@register.inclusion_tag('chatbot/_chat_message.html')
def chat_message(message, role='bot'):
    """
    Renderiza uma mensagem do chat
    Usage: {% chat_message message=m.content role=m.role %}
    """
    return {
        'message': message,
        'role': role,
    }


@register.simple_tag
def csrf_token_value(request):
    """
    Retorna o valor do CSRF token para uso em JavaScript
    Usage: const csrfToken = '{% csrf_token_value request %}';
    """
    from django.middleware.csrf import get_token
    return get_token(request)
