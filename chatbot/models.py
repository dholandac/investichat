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

	def __str__(self) -> str:
		return f"{self.role}: {self.content[:40]}"
