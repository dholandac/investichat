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
