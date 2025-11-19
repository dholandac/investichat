from django.contrib import admin
from .models import Conversation, Message, Portfolio, Transaction, PortfolioSnapshot

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

# Inline para exibir transações relacionadas em um portfolio
class TransactionInline(admin.TabularInline):
	model = Transaction
	extra = 0
	readonly_fields = ('created_at',)

# Registro dos modelos de Portfolio
@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'created_at', 'updated_at')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('user__username',)
	inlines = [TransactionInline]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
	list_display = ('id', 'portfolio', 'symbol', 'transaction_type', 'quantity', 'price', 'created_at')
	list_filter = ('transaction_type', 'created_at', 'symbol')
	search_fields = ('symbol', 'portfolio__user__username', 'notes')
	readonly_fields = ('created_at',)

@admin.register(PortfolioSnapshot)
class PortfolioSnapshotAdmin(admin.ModelAdmin):
	list_display = ('id', 'portfolio', 'total_value', 'total_cost', 'profit_loss', 'profit_loss_percent', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('portfolio__user__username',)
	readonly_fields = ('created_at',)
