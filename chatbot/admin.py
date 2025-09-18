from django.contrib import admin
from .models import Conversation, Message

# Inline para exibir mensagens relacionadas em uma conversa
class MessageInline(admin.TabularInline):
	model = Message
	extra = 0
	readonly_fields = ('role', 'content', 'created_at')

# Registro dos modelos no admin
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'title', 'created_at', 'updated_at')
	list_filter = ('user',)
	search_fields = ('user__username', 'title')
	inlines = [MessageInline]

# Registro do modelo Message com exibição personalizada
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'conversation', 'role', 'short_content', 'created_at')
	list_filter = ('role', 'conversation__user')
	search_fields = ('content',)

	def short_content(self, obj):
		return obj.content[:60]
