from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db import transaction as db_transaction
import json
import os
import re
import logging
from dotenv import load_dotenv
from .models import Portfolio, Transaction, PortfolioSnapshot
from .finnhub_client import FinnhubAPIClient

load_dotenv()

# Logger para depuração
logger = logging.getLogger(__name__)


def get_api_key():
    """Obtém a chave da API do Finnhub"""
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        raise ValueError("FINNHUB_API_KEY não configurada")
    return api_key


def get_quote_cached(symbol, api_key):
    """
    Busca cotação com cache de 60 segundos.
    Similar ao get_stock_quote_cached usado no chatbot.
    """
    cache_key = f'portfolio_quote_{symbol}'
    quote = cache.get(cache_key)
    
    if quote is None:
        try:
            client = FinnhubAPIClient(api_key)
            quote = client.get_global_quote(symbol)
            if quote:
                # Armazena no cache por 60 segundos
                cache.set(cache_key, quote, timeout=60)
                logger.debug(f"Cache MISS para {symbol} - buscado da API")
            else:
                logger.warning(f"Cotação não encontrada para {symbol}")
        except Exception as e:
            logger.error(f"Erro ao buscar cotação para {symbol}: {e}")
            return None
    else:
        logger.debug(f"Cache HIT para {symbol} - retornado do cache")
    
    return quote


@login_required
def portfolio_view(request):
    """View principal para visualizar a carteira"""
    portfolio, created = Portfolio.objects.get_or_create(user=request.user)
    
    # Obtém todas as transações
    transactions = portfolio.transactions.all()
    
    # Calcula posições atuais (agrupando compras e vendas)
    holdings = {}
    for trans in transactions:
        symbol = trans.symbol
        if symbol not in holdings:
            holdings[symbol] = {
                'quantity': 0,
                'total_cost': 0.0,
                'transactions': []
            }
        
        if trans.transaction_type == 'BUY':
            holdings[symbol]['quantity'] += float(trans.quantity)
            holdings[symbol]['total_cost'] += float(trans.price * trans.quantity)
            holdings[symbol]['transactions'].append(trans)
        elif trans.transaction_type == 'SELL':
            # CORREÇÃO: Calcula o custo médio ANTES de subtrair a quantidade
            # Isso evita divisão por zero e garante cálculo correto
            quantity_before = holdings[symbol]['quantity']
            if quantity_before > 0:
                avg_cost = holdings[symbol]['total_cost'] / quantity_before
                cost_to_remove = avg_cost * float(trans.quantity)
                holdings[symbol]['total_cost'] -= cost_to_remove
            else:
                # Se não há quantidade, não há custo para remover
                logger.warning(f"Tentativa de vender {trans.quantity} {symbol} sem posição disponível")
            
            holdings[symbol]['quantity'] -= float(trans.quantity)
            holdings[symbol]['transactions'].append(trans)
    
    # Remove posições zeradas
    holdings = {k: v for k, v in holdings.items() if v['quantity'] > 0}
    
    # Busca cotações atuais (com cache)
    try:
        api_key = get_api_key()
    except ValueError as e:
        logger.error(f"Erro ao obter API key: {e}")
        context = {
            'portfolio': portfolio,
            'holdings': [],
            'transactions': transactions[:20],
            'total_value': 0,
            'total_cost': 0,
            'total_profit_loss': 0,
            'total_profit_loss_percent': 0,
            'show_sidebar': True,
            'error_message': 'Erro ao conectar com a API de cotações. Tente novamente mais tarde.',
        }
        return render(request, 'chatbot/portfolio.html', context)
    
    portfolio_data = []
    for symbol, data in holdings.items():
        quote = get_quote_cached(symbol, api_key)
        if quote:
            current_price_usd = quote.current_price
            current_value_usd = current_price_usd * data['quantity']
            avg_price_usd = data['total_cost'] / data['quantity'] if data['quantity'] > 0 else 0
            profit_loss_usd = current_value_usd - data['total_cost']
            profit_loss_percent = (profit_loss_usd / data['total_cost'] * 100) if data['total_cost'] > 0 else 0
            
            portfolio_data.append({
                'symbol': symbol,
                'quantity': data['quantity'],
                'avg_price': avg_price_usd,
                'current_price': current_price_usd,
                'current_value': current_value_usd,
                'total_cost': data['total_cost'],
                'profit_loss': profit_loss_usd,
                'profit_loss_percent': profit_loss_percent,
                'change_percent': quote.change_percent,
            })
    
    # Ordena por valor atual (maior primeiro)
    portfolio_data.sort(key=lambda x: x['current_value'], reverse=True)
    
    # Calcula totais
    total_value = sum(item['current_value'] for item in portfolio_data)
    total_cost = sum(item['total_cost'] for item in portfolio_data)
    total_profit_loss = total_value - total_cost
    total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
    
    context = {
        'portfolio': portfolio,
        'holdings': portfolio_data,
        'transactions': transactions[:20],  # Últimas 20 transações
        'total_value': total_value,
        'total_cost': total_cost,
        'total_profit_loss': total_profit_loss,
        'total_profit_loss_percent': total_profit_loss_percent,
        'show_sidebar': True,  # Habilita o sidebar
    }
    
    return render(request, 'chatbot/portfolio.html', context)


@login_required
@require_http_methods(["POST"])
def add_transaction(request):
    """Adiciona uma nova transação (compra ou venda)"""
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').upper().strip()
        transaction_type = data.get('transaction_type', 'BUY')
        quantity = float(data.get('quantity', 0))
        price = float(data.get('price', 0))
        notes = data.get('notes', '')
        
        if not symbol or quantity <= 0 or price <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Dados inválidos. Verifique símbolo, quantidade e preço.'
            }, status=400)
        
        if transaction_type not in ['BUY', 'SELL']:
            return JsonResponse({
                'status': 'error',
                'message': 'Tipo de transação inválido. Use BUY ou SELL.'
            }, status=400)
        
        # Validação básica do formato do símbolo
        if not re.match(r'^[A-Z0-9\.\-]+$', symbol) or len(symbol) < 1 or len(symbol) > 10:
            return JsonResponse({
                'status': 'error',
                'message': f'Símbolo {symbol} inválido. Use apenas letras, números, pontos e hífens (ex: AAPL, MSFT, TSLA).'
            }, status=400)
        
        # Verifica se o símbolo existe na API e tem dados válidos (com cache)
        try:
            api_key = get_api_key()
        except ValueError as e:
            logger.error(f"Erro ao obter API key: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Erro ao conectar com a API de cotações. Tente novamente mais tarde.'
            }, status=500)
        
        quote = get_quote_cached(symbol, api_key)
        
        if not quote:
            return JsonResponse({
                'status': 'error',
                'message': f'Símbolo {symbol} não encontrado ou inválido. Verifique se o símbolo está correto.'
            }, status=404)
        
        # Valida se a cotação tem preço válido (maior que zero)
        if quote.current_price <= 0:
            return JsonResponse({
                'status': 'error',
                'message': f'Símbolo {symbol} não possui cotação válida. Preço atual é zero ou inválido.'
            }, status=400)
        
        # Para vendas, verifica se há quantidade suficiente
        if transaction_type == 'SELL':
            portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
            holdings = {}
            for trans in portfolio.transactions.all():
                if trans.symbol == symbol:
                    if trans.transaction_type == 'BUY':
                        holdings[symbol] = holdings.get(symbol, 0) + float(trans.quantity)
                    elif trans.transaction_type == 'SELL':
                        holdings[symbol] = holdings.get(symbol, 0) - float(trans.quantity)
            
            available_quantity = holdings.get(symbol, 0)
            if available_quantity < quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Quantidade insuficiente. Você possui {available_quantity} {symbol}.'
                }, status=400)
        
        # Cria a transação
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
        transaction = Transaction.objects.create(
            portfolio=portfolio,
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            notes=notes
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Transação {transaction_type} de {quantity} {symbol} registrada com sucesso!',
            'transaction_id': transaction.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao processar dados JSON.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao adicionar transação: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_portfolio_data(request):
    """Retorna dados da carteira em formato JSON para AJAX"""
    try:
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
        
        # Calcula posições
        holdings = {}
        for trans in portfolio.transactions.all():
            symbol = trans.symbol
            if symbol not in holdings:
                holdings[symbol] = {'quantity': 0, 'total_cost': 0.0}
            
            if trans.transaction_type == 'BUY':
                holdings[symbol]['quantity'] += float(trans.quantity)
                holdings[symbol]['total_cost'] += float(trans.price * trans.quantity)
            elif trans.transaction_type == 'SELL':
                # CORREÇÃO: Calcula o custo médio ANTES de subtrair a quantidade
                quantity_before = holdings[symbol]['quantity']
                if quantity_before > 0:
                    avg_cost = holdings[symbol]['total_cost'] / quantity_before
                    cost_to_remove = avg_cost * float(trans.quantity)
                    holdings[symbol]['total_cost'] -= cost_to_remove
                holdings[symbol]['quantity'] -= float(trans.quantity)
        
        holdings = {k: v for k, v in holdings.items() if v['quantity'] > 0}
        
        # Busca cotações (com cache)
        try:
            api_key = get_api_key()
        except ValueError as e:
            logger.error(f"Erro ao obter API key: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Erro ao conectar com a API de cotações.'
            }, status=500)
        
        portfolio_data = []
        for symbol, data in holdings.items():
            quote = get_quote_cached(symbol, api_key)
            if quote:
                current_price_usd = quote.current_price
                current_value_usd = current_price_usd * data['quantity']
                avg_price_usd = data['total_cost'] / data['quantity'] if data['quantity'] > 0 else 0
                profit_loss_usd = current_value_usd - data['total_cost']
                profit_loss_percent = (profit_loss_usd / data['total_cost'] * 100) if data['total_cost'] > 0 else 0
                
                portfolio_data.append({
                    'symbol': symbol,
                    'quantity': data['quantity'],
                    'avg_price': avg_price_usd,
                    'current_price': current_price_usd,
                    'current_value': current_value_usd,
                    'total_cost': data['total_cost'],
                    'profit_loss': profit_loss_usd,
                    'profit_loss_percent': profit_loss_percent,
                    'change_percent': quote.change_percent,
                })
        
        total_value = sum(item['current_value'] for item in portfolio_data)
        total_cost = sum(item['total_cost'] for item in portfolio_data)
        total_profit_loss = total_value - total_cost
        total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'holdings': portfolio_data,
                'total_value': total_value,
                'total_cost': total_cost,
                'total_profit_loss': total_profit_loss,
                'total_profit_loss_percent': total_profit_loss_percent,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao obter dados da carteira: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_portfolio_history(request):
    """Retorna histórico de valorização da carteira para gráfico"""
    try:
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
        
        # Busca snapshots existentes
        snapshots = portfolio.snapshots.all().order_by('created_at')[:30]  # Últimos 30 snapshots
        
        # Se não houver snapshots, cria um atual
        if not snapshots.exists():
            try:
                total_value = portfolio.get_total_value()
                total_cost = portfolio.get_total_cost()
                profit_loss = portfolio.get_profit_loss()
                profit_loss_percent = portfolio.get_profit_loss_percent()
                
                # Só cria snapshot se houver valor (evita snapshots zerados)
                if total_value > 0 or total_cost > 0:
                    PortfolioSnapshot.objects.create(
                        portfolio=portfolio,
                        total_value=total_value,
                        total_cost=total_cost,
                        profit_loss=profit_loss,
                        profit_loss_percent=profit_loss_percent
                    )
                    # Recarrega os snapshots
                    snapshots = portfolio.snapshots.all().order_by('created_at')[:30]
                else:
                    # Se não há valor, retorna lista vazia
                    return JsonResponse({
                        'status': 'success',
                        'data': []
                    })
            except Exception as e:
                logger.error(f"Erro ao criar snapshot inicial: {e}", exc_info=True)
                # Se falhar, retorna lista vazia em vez de erro
                return JsonResponse({
                    'status': 'success',
                    'data': []
                })
        
        history_data = []
        for snapshot in snapshots:
            # Converte Decimal para float explicitamente
            total_value = float(snapshot.total_value) if snapshot.total_value else 0.0
            total_cost = float(snapshot.total_cost) if snapshot.total_cost else 0.0
            profit_loss = float(snapshot.profit_loss) if snapshot.profit_loss else 0.0
            profit_loss_percent = float(snapshot.profit_loss_percent) if snapshot.profit_loss_percent else 0.0
            
            history_data.append({
                'date': snapshot.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_value': total_value,
                'total_cost': total_cost,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
            })
        
        return JsonResponse({
            'status': 'success',
            'data': history_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao obter histórico: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def create_snapshot(request):
    """Cria um snapshot atual da carteira"""
    try:
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
        
        total_value = portfolio.get_total_value()
        total_cost = portfolio.get_total_cost()
        profit_loss = portfolio.get_profit_loss()
        profit_loss_percent = portfolio.get_profit_loss_percent()
        
        snapshot = PortfolioSnapshot.objects.create(
            portfolio=portfolio,
            total_value=total_value,
            total_cost=total_cost,
            profit_loss=profit_loss,
            profit_loss_percent=profit_loss_percent
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Snapshot criado com sucesso!',
            'snapshot_id': snapshot.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao criar snapshot: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_stock_price(request, symbol):
    """Retorna o preço atual de um símbolo para preencher automaticamente no formulário"""
    try:
        api_key = get_api_key()
        quote = get_quote_cached(symbol.upper().strip(), api_key)
        
        if quote:
            return JsonResponse({
                'status': 'success',
                'price': quote.current_price,
                'symbol': quote.symbol,
                'change_percent': quote.change_percent,
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Símbolo {symbol} não encontrado ou inválido.'
            }, status=404)
            
    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao conectar com a API de cotações.'
        }, status=500)
    except Exception as e:
        logger.error(f"Erro ao buscar preço para {symbol}: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao buscar preço: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def reset_portfolio(request):
    """Reseta a carteira virtual, deletando todas as transações e snapshots"""
    try:
        portfolio = get_object_or_404(Portfolio, user=request.user)
        
        # Conta quantas transações e snapshots serão deletados
        transactions_count = portfolio.transactions.count()
        snapshots_count = portfolio.snapshots.count()
        
        # Deleta todas as transações (isso também deleta os snapshots relacionados via CASCADE)
        portfolio.transactions.all().delete()
        portfolio.snapshots.all().delete()
        
        logger.info(f"Carteira {portfolio.id} resetada: {transactions_count} transações e {snapshots_count} snapshots deletados")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Carteira resetada com sucesso! {transactions_count} transação(ões) e {snapshots_count} snapshot(s) foram removidos.',
        })
        
    except Exception as e:
        logger.error(f"Erro ao resetar carteira: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao resetar carteira: {str(e)}'
        }, status=500)

