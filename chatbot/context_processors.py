"""
Context processors para tornar dados disponíveis globalmente nos templates
"""
from .models import UserStockSelection


def stock_choices(request):
    """Disponibiliza as escolhas de ações em todos os templates"""
    choices = [
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
    
    # Obtém as ações selecionadas pelo usuário, se autenticado
    selected_stocks = []
    if request.user.is_authenticated:
        try:
            selection = UserStockSelection.objects.get(user=request.user)
            selected_stocks = selection.get_stock_list()
        except UserStockSelection.DoesNotExist:
            selected_stocks = ['AAPL', 'MSFT', 'TSLA']  # Padrão
    
    return {
        'available_stocks': choices,
        'selected_stocks': selected_stocks,
    }
