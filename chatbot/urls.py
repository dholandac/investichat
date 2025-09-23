from django.urls import path
from . import views
from . import investment_views

urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('chat/', views.chat_message, name='chat_message'),
    path('investment-data/', investment_views.get_investment_data, name='investment_data'),
    path('stock-quote/<str:symbol>/', investment_views.get_stock_quote, name='stock_quote'),
    path('time-series/<str:symbol>/', investment_views.get_time_series, name='time_series'),
    path('save-stock-selection/', views.save_stock_selection, name='save_stock_selection'),
    path('get-stock-selection/', views.get_stock_selection, name='get_stock_selection'),
]

