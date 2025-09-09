from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_django
from django.contrib.auth import logout as logout_django
from django.contrib.auth.decorators import login_required

def cadastro(request):
    if request.method == "GET":
        return render(request, 'cadastro.html')
    else:
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        if not username or not email or not senha:
            return render(request, 'cadastro.html', {'mensagem': 'Preencha todos os campos!'})

        user = User.objects.filter(username=username).first()

        if user:
            return render(request, 'cadastro.html', {'mensagem': 'Já existe um usuário com esse nome de usuário!'})
        
        user = User.objects.create_user(username=username, email=email, password=senha)
        user.save()

        return redirect('login')


def login(request):
    if request.method == "GET":
            return render(request, 'login.html')
    else:
        username = request.POST.get('username')
        senha = request.POST.get('senha')

        user = authenticate(username=username, password=senha)

        if user:
             login_django(request, user)

             return redirect('/chatbot/')
        else:
             return render(request, 'login.html', {'mensagem': 'Email ou senha inválidos!'})

def logout(request):
    logout_django(request)
    return redirect('login')