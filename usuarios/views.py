from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_django
from django.contrib.auth import logout as logout_django
from django.contrib.auth.decorators import login_required
from .models import PerfilUsuario
from chatbot.models import Conversation

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

        # Verifica tamanho mínimo da senha
        if len(senha) < 8:
            return render(request, 'cadastro.html', {'mensagem': 'A senha deve ter pelo menos 8 caracteres!'})

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

# Lógica da conta do usuário
@login_required(login_url="/auth/login/")
def account(request):
    mensagem = None
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'update_email':
            novo_email = (request.POST.get('email') or '').strip()
            if not novo_email:
                mensagem = 'Informe um email válido.'
            else:
                existe = User.objects.filter(email__iexact=novo_email).exclude(pk=request.user.pk).exists()
                if existe:
                    mensagem = 'Este email já está em uso por outro usuário.'
                else:
                    request.user.email = novo_email
                    request.user.save()
                    mensagem = 'Email atualizado com sucesso!'
        elif action == 'update_password':
            senha_atual = request.POST.get('senha_atual')
            nova_senha = request.POST.get('nova_senha')
            confirma_senha = request.POST.get('confirma_senha')
            if not senha_atual or not nova_senha or not confirma_senha:
                mensagem = 'Preencha todos os campos da senha.'
            elif not request.user.check_password(senha_atual):
                mensagem = 'Senha atual incorreta.'
            elif nova_senha != confirma_senha:
                mensagem = 'A nova senha e a confirmação não coincidem.'
            elif len(nova_senha) < 8:
                mensagem = 'A nova senha deve ter pelo menos 8 caracteres.'
            else:
                request.user.set_password(nova_senha)
                request.user.save()
                mensagem = 'Senha atualizada com sucesso!'
                # Reautentica o usuário após troca de senha
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
        elif action == 'update_perfil_investidor':
            novo_perfil = request.POST.get('perfil_investidor')
            if novo_perfil not in ['CONSERVADOR', 'MODERADO', 'AGRESSIVO']:
                mensagem = 'Selecione um perfil válido.'
            else:
                perfil_usuario, _ = PerfilUsuario.objects.get_or_create(user=request.user)
                perfil_usuario.perfil_investidor = novo_perfil
                perfil_usuario.save()
                mensagem = 'Perfil de investidor atualizado com sucesso!'
        elif action == 'clear_chat_history':
            # Limpa todo o histórico de chat do usuário (conversas e mensagens)
            Conversation.objects.filter(user=request.user).delete()
            mensagem = 'Histórico de chat apagado com sucesso!'

    # Adiciona perfilusuario ao contexto
    perfilusuario = None
    try:
        perfilusuario = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        perfilusuario = None
    return render(request, 'account.html', {'mensagem': mensagem, 'user': request.user, 'perfilusuario': perfilusuario})

@login_required(login_url="/auth/login/")
def questionario_perfil(request):
    user_profile, created = PerfilUsuario.objects.get_or_create(user=request.user)

    if user_profile.questionario_completo:
        return redirect("chatbot") # Redireciona para o chatbot se o questionário já foi preenchido

    if request.method == "POST":
        pontuacao = 0
        for i in range(1, 11):
            resposta = request.POST.get(f'pergunta_{i}')
            if resposta == 'A':
                pontuacao += 1
            elif resposta == 'B':
                pontuacao += 2
            elif resposta == 'C':
                pontuacao += 3
        
        if 10 <= pontuacao <= 16:
            perfil = 'CONSERVADOR'
        elif 17 <= pontuacao <= 23:
            perfil = 'MODERADO'
        else:
            perfil = 'AGRESSIVO'

        user_profile.perfil_investidor = perfil
        user_profile.questionario_completo = True
        user_profile.save()

        return JsonResponse({"success": True, "perfil": perfil})

    return render(request, "usuarios/questionario_perfil.html")
