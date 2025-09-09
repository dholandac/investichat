from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Bloqueia a acesso do usuário caso ele não esteja logado, o enviando de volta para a página de login
@login_required(login_url="/auth/login/")
def chatbot(request):
    return render(request, 'chatbot/chatbot.html')