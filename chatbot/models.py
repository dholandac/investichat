from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Modelo para conversas entre o usuário e o chatbot
class Conversation(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
	title = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-updated_at']
		indexes = [
			models.Index(fields=['user', '-updated_at']),  # Query mais comum: buscar conversas do usuário
			models.Index(fields=['-created_at']),
		]

	def __str__(self) -> str:
		return self.title or f"Conversa de {self.user.username} em {self.created_at:%Y-%m-%d %H:%M}"

# Modelo para mensagens dentro de uma conversa
class Message(models.Model):
	ROLE_CHOICES = (
		('user', 'User'),
		('bot', 'Bot'),
	)

	conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
	role = models.CharField(max_length=10, choices=ROLE_CHOICES)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']
		indexes = [
			models.Index(fields=['conversation', 'created_at']),  # Buscar mensagens de uma conversa
			models.Index(fields=['conversation', '-created_at']),  # Ordem reversa
		]

	def __str__(self) -> str:
		return f"{self.role}: {self.content[:40]}"
	
# Modelo para armazenar as ações selecionadas pelo usuário
class UserStockSelection(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stock_selection')
	selected_stocks = models.CharField(max_length=255, blank=True, help_text='Símbolos das ações separados por vírgula')
	updated_at = models.DateTimeField(auto_now=True)

	def get_stock_list(self):
		"""Retorna lista de símbolos de ações"""
		if not self.selected_stocks:
			return []
		return [s.strip() for s in self.selected_stocks.split(',') if s.strip()]

	def set_stock_list(self, stock_list):
		"""Define lista de símbolos de ações"""
		if isinstance(stock_list, list):
			self.selected_stocks = ','.join([s.strip() for s in stock_list if s.strip()])
		else:
			self.selected_stocks = ''
		self.save()

	def __str__(self):
		return f"Seleção de ações de {self.user.username}: {self.selected_stocks}"


# Modelos para Carteira Virtual (Mock Portfolio)

class Portfolio(models.Model):
	"""Representa a carteira virtual de um usuário"""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-updated_at']
	
	def __str__(self):
		return f"Carteira de {self.user.username}"
	
	def get_total_value(self):
		"""Calcula o valor total atual da carteira (com cache)"""
		from .finnhub_client import FinnhubAPIClient
		from django.core.cache import cache
		import os
		import logging
		from dotenv import load_dotenv
		load_dotenv()
		
		logger = logging.getLogger(__name__)
		api_key = os.getenv('FINNHUB_API_KEY')
		if not api_key:
			logger.warning("FINNHUB_API_KEY não configurada")
			return 0.0
		
		client = FinnhubAPIClient(api_key)
		total_value = 0.0
		
		# Agrupa transações por símbolo para calcular quantidade total
		holdings = {}
		for transaction in self.transactions.filter(transaction_type='BUY'):
			symbol = transaction.symbol
			if symbol not in holdings:
				holdings[symbol] = 0
			holdings[symbol] += transaction.quantity
		
		for transaction in self.transactions.filter(transaction_type='SELL'):
			symbol = transaction.symbol
			if symbol in holdings:
				holdings[symbol] -= transaction.quantity
				if holdings[symbol] <= 0:
					del holdings[symbol]
		
		# Calcula valor atual de cada posição (com cache)
		for symbol, quantity in holdings.items():
			cache_key = f'portfolio_quote_{symbol}'
			quote = cache.get(cache_key)
			
			if quote is None:
				try:
					quote = client.get_global_quote(symbol)
					if quote:
						cache.set(cache_key, quote, timeout=60)
				except Exception as e:
					logger.error(f"Erro ao buscar cotação para {symbol}: {e}")
					continue
			
			if quote:
				total_value += quote.current_price * quantity
		
		return total_value
	
	def get_total_cost(self):
		"""Calcula o custo total investido (soma de todas as compras)"""
		total_cost = 0.0
		for transaction in self.transactions.filter(transaction_type='BUY'):
			total_cost += transaction.price * transaction.quantity
		return total_cost
	
	def get_profit_loss(self):
		"""Calcula lucro/prejuízo total"""
		return self.get_total_value() - self.get_total_cost()
	
	def get_profit_loss_percent(self):
		"""Calcula percentual de lucro/prejuízo"""
		total_cost = self.get_total_cost()
		if total_cost == 0:
			return 0.0
		return (self.get_profit_loss() / total_cost) * 100


class Transaction(models.Model):
	"""Representa uma transação de compra ou venda de ativo"""
	TRANSACTION_TYPES = (
		('BUY', 'Compra'),
		('SELL', 'Venda'),
	)
	
	portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
	symbol = models.CharField(max_length=20, help_text='Símbolo do ativo (ex: AAPL, MSFT)')
	transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
	quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text='Quantidade de ações/ativos')
	price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Preço unitário na transação')
	created_at = models.DateTimeField(auto_now_add=True)
	notes = models.TextField(blank=True, help_text='Notas opcionais sobre a transação')
	
	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['portfolio', '-created_at']),
			models.Index(fields=['symbol']),
		]
	
	def __str__(self):
		return f"{self.transaction_type} {self.quantity} {self.symbol} @ {self.price} em {self.created_at:%Y-%m-%d}"


class PortfolioSnapshot(models.Model):
	"""Snapshot da carteira em um momento específico para histórico de valorização"""
	portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='snapshots')
	total_value = models.DecimalField(max_digits=12, decimal_places=2)
	total_cost = models.DecimalField(max_digits=12, decimal_places=2)
	profit_loss = models.DecimalField(max_digits=12, decimal_places=2)
	profit_loss_percent = models.DecimalField(max_digits=6, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['portfolio', '-created_at']),
		]
	
	def __str__(self):
		return f"Snapshot de {self.portfolio.user.username} em {self.created_at:%Y-%m-%d %H:%M}"