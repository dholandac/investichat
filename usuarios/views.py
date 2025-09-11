from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_django
from django.contrib.auth import logout as logout_django
from django.contrib.auth.decorators import login_required

# Lógica de cadastro
def cadastro(request):
    # Se o usuário apenas está acessando, exiba a página
    if request.method == "GET":
        return render(request, 'cadastro.html')
    # Caso contrário, procede com o processo de cadastro
    else:
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        # Verifica se todos os campos foram preenchidos
        if not username or not email or not senha:
            return render(request, 'cadastro.html', {'mensagem': 'Preencha todos os campos!'})

        # Verifica se já existe um usuário com esse username
        user = User.objects.filter(username=username).first()

        # Envia uma mensagem para o html caso a mensagem já exista
        if user:
            return render(request, 'cadastro.html', {'mensagem': 'Já existe um usuário com esse nome de usuário!'})
        
        # Cria o usuário e o salva
        user = User.objects.create_user(username=username, email=email, password=senha)
        user.save()

        return redirect('login')

# Lógica de login
def login(request):
    # Se o usuário apenas está acessando, exiba a página
    if request.method == "GET":
            return render(request, 'login.html')
    # Caso contrário, procede com o processo de login
    else:
        # Busca pelo username e senha inseridos
        username = request.POST.get('username')
        senha = request.POST.get('senha')

        # Procede autenticando o usuário
        user = authenticate(username=username, password=senha)

        if user:
             login_django(request, user)

             return redirect('/chatbot/')
        else:
             return render(request, 'login.html', {'mensagem': 'Email ou senha inválidos!'})

# Lógica de logout
def logout(request):
    logout_django(request)
    return redirect('login')

@login_required(login_url="/auth/login/")
def account(request):
    if request.method == "GET":
            return render(request, 'account.html')