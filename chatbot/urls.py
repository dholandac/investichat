from django.urls import path
from . import views
from . import investment_views
from . import portfolio_views

urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('chat/', views.chat_message, name='chat_message'),
    path('investment-data/', investment_views.get_investment_data, name='investment_data'),
    path('stock-quote/<str:symbol>/', investment_views.get_stock_quote, name='stock_quote'),
    path('time-series/<str:symbol>/', investment_views.get_time_series, name='time_series'),
    path('save-stock-selection/', views.save_stock_selection, name='save_stock_selection'),
    path('get-stock-selection/', views.get_stock_selection, name='get_stock_selection'),
    path('refresh-investment/', views.refresh_investment_panel, name='refresh_investment_panel'),
    # Portfolio URLs
    path('portfolio/', portfolio_views.portfolio_view, name='portfolio'),
    path('portfolio/add-transaction/', portfolio_views.add_transaction, name='add_transaction'),
    path('portfolio/data/', portfolio_views.get_portfolio_data, name='get_portfolio_data'),
    path('portfolio/history/', portfolio_views.get_portfolio_history, name='get_portfolio_history'),
    path('portfolio/snapshot/', portfolio_views.create_snapshot, name='create_snapshot'),
    path('portfolio/reset/', portfolio_views.reset_portfolio, name='reset_portfolio'),
    path('portfolio/stock-price/<str:symbol>/', portfolio_views.get_stock_price, name='get_stock_price'),
]

