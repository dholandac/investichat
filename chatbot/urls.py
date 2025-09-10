from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('chat/', views.chat_message, name='chat_message'),
]

