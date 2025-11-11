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
from chatbot.models import Conversation, Message
import re


def handler404(request, exception):
    """Handler customizado para erro 404"""
    return render(request, '404.html', {'show_sidebar': True}, status=404)


def traduzir_erro_senha(mensagem):
    """Traduz mensagens de erro de senha do Django para português"""
    traducoes = {
        'This password is too short. It must contain at least 8 characters.': 
            'Esta senha é muito curta. Ela deve conter pelo menos 8 caracteres.',
        'This password is too common.': 
            'Esta senha é muito comum. Escolha uma senha mais segura.',
        'This password is entirely numeric.': 
            'Esta senha é inteiramente numérica. Use letras e números.',
        'The password is too similar to the username.': 
            'A senha é muito similar ao nome de usuário.',
        'The password is too similar to the email address.': 
            'A senha é muito similar ao endereço de email.',
    }
    # Verifica tradução exata
    if mensagem in traducoes:
        return traducoes[mensagem]
    # Verifica se contém palavras-chave para tradução parcial
    if 'too short' in mensagem.lower() or 'must contain at least' in mensagem.lower():
        return 'Esta senha é muito curta. Ela deve conter pelo menos 8 caracteres.'
    if 'too common' in mensagem.lower():
        return 'Esta senha é muito comum. Escolha uma senha mais segura.'
    if 'entirely numeric' in mensagem.lower():
        return 'Esta senha é inteiramente numérica. Use letras e números.'
    if 'too similar to the username' in mensagem.lower():
        return 'A senha é muito similar ao nome de usuário.'
    if 'too similar to the email' in mensagem.lower():
        return 'A senha é muito similar ao endereço de email.'
    # Retorna a mensagem original se não encontrar tradução
    return mensagem

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
        confirma_senha = request.POST.get('confirma_senha')

        # Verifica se todos os campos foram preenchidos
        if not username or not email or not senha or not confirma_senha:
            return render(request, 'cadastro.html', {'mensagem': 'Preencha todos os campos!'})

        # Valida o nome de usuário
        username = username.strip()
        
        # Tamanho mínimo e máximo
        if len(username) < 4:
            return render(request, 'cadastro.html', {'mensagem': 'O nome de usuário deve ter pelo menos 4 caracteres!'})
        
        if len(username) > 15:
            return render(request, 'cadastro.html', {'mensagem': 'O nome de usuário deve ter no máximo 15 caracteres!'})
        
        # Apenas letras, números, underscore e hífen são permitidos
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return render(request, 'cadastro.html', {'mensagem': 'O nome de usuário pode conter apenas letras, números, underscore (_) e hífen (-)!'})
        
        # Não pode começar ou terminar com underscore ou hífen
        if username.startswith('_') or username.startswith('-') or username.endswith('_') or username.endswith('-'):
            return render(request, 'cadastro.html', {'mensagem': 'O nome de usuário não pode começar ou terminar com underscore (_) ou hífen (-)!'})
        
        # Não pode ter caracteres especiais consecutivos
        if re.search(r'[_-]{2,}', username):
            return render(request, 'cadastro.html', {'mensagem': 'O nome de usuário não pode ter underscore (_) ou hífen (-) consecutivos!'})

        # Verifica se as senhas coincidem
        if senha != confirma_senha:
            return render(request, 'cadastro.html', {
                'mensagem': 'As senhas não coincidem!',
                'username': username,
                'email': email
            })

        # Verifica se já existe um usuário com esse username
        user = User.objects.filter(username=username).first()

        # Envia uma mensagem para o html caso o usuário já exista
        if user:
            return render(request, 'cadastro.html', {
                'mensagem': 'Já existe um usuário com esse nome de usuário!',
                'username': username,
                'email': email
            })
        
        # Valida a senha usando os validadores do Django
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        try:
            validate_password(senha, User(username=username, email=email))
        except ValidationError as e:
            # Traduz as mensagens de erro para português
            mensagens_traduzidas = [traduzir_erro_senha(msg) for msg in e.messages]
            mensagem_erro = '; '.join(mensagens_traduzidas)
            return render(request, 'cadastro.html', {
                'mensagem': mensagem_erro,
                'username': username,
                'email': email
            })
        
        # Cria o usuário e o salva
        try:
            user = User.objects.create_user(username=username, email=email, password=senha)
            user.save()
        except Exception as e:
            # Trata exceções do Django que podem ter mensagens em inglês
            from django.db import IntegrityError
            
            mensagem_erro = str(e)
            
            # Traduz mensagens de erro comuns
            if 'username' in mensagem_erro.lower() and ('unique' in mensagem_erro.lower() or 'already exists' in mensagem_erro.lower()):
                mensagem_erro = 'Já existe um usuário com esse nome de usuário!'
            elif 'email' in mensagem_erro.lower() and ('unique' in mensagem_erro.lower() or 'already exists' in mensagem_erro.lower()):
                mensagem_erro = 'Este email já está em uso por outro usuário!'
            elif isinstance(e, IntegrityError):
                mensagem_erro = 'Erro ao criar usuário. Verifique se o nome de usuário ou email já estão em uso.'
            else:
                mensagem_erro = 'Erro ao criar usuário. Por favor, tente novamente.'
            
            return render(request, 'cadastro.html', {
                'mensagem': mensagem_erro,
                'username': username,
                'email': email
            })

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
            else:
                # Valida a senha usando os validadores do Django
                from django.contrib.auth.password_validation import validate_password
                from django.core.exceptions import ValidationError
                
                try:
                    validate_password(nova_senha, request.user)
                except ValidationError as e:
                    # Traduz as mensagens de erro para português
                    mensagens_traduzidas = [traduzir_erro_senha(msg) for msg in e.messages]
                    mensagem = '; '.join(mensagens_traduzidas)
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
    return render(request, 'account.html', {'mensagem': mensagem, 'user': request.user, 'perfilusuario': perfilusuario, 'show_sidebar': True})

@login_required(login_url="/auth/login/")
def questionario_perfil(request):
    from chatbot.forms import QuestionarioPerfil
    
    user_profile, created = PerfilUsuario.objects.get_or_create(user=request.user)

    if user_profile.questionario_completo:
        return redirect("chatbot")  # Redireciona para o chatbot se o questionário já foi preenchido

    if request.method == "POST":
        form = QuestionarioPerfil(request.POST)
        
        if form.is_valid():
            perfil = form.calcular_perfil()
            
            if perfil:
                user_profile.perfil_investidor = perfil.upper()
                user_profile.questionario_completo = True
                user_profile.save()
                
                return JsonResponse({"success": True, "perfil": perfil})
            else:
                return JsonResponse({"success": False, "error": "Erro ao calcular perfil"}, status=400)
        else:
            return JsonResponse({"success": False, "error": "Formulário inválido"}, status=400)

    return render(request, "usuarios/questionario_perfil.html")

@login_required(login_url="/auth/login/")
def admin_panel(request):
    """Página de administração - apenas para usuários com is_staff=True"""
    # Verifica se o usuário tem permissão de administrador
    if not request.user.is_staff:
        return redirect('account')
    
    mensagem = None
    
    # Processa ações POST
    if request.method == "POST":
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            target_user = User.objects.get(id=user_id)
            
            if action == 'delete_history':
                # Deleta todas as conversas e mensagens do usuário
                conversations = Conversation.objects.filter(user=target_user)
                message_count = Message.objects.filter(conversation__user=target_user).count()
                conversations.delete()  # CASCADE deleta as mensagens automaticamente
                mensagem = f'Sucesso: Histórico do usuário {target_user.username} excluído com sucesso! ({message_count} mensagens removidas)'
            
            elif action == 'delete_user':
                # Deleta o usuário e todos os dados relacionados (CASCADE)
                if target_user == request.user:
                    mensagem = 'Erro: Você não pode excluir o seu próprio perfil enquanto estiver logado.'
                else:
                    username = target_user.username
                    target_user.delete()  # CASCADE deleta PerfilUsuario, Conversation, Message, etc.
                    mensagem = f'Sucesso: Usuário {username} e todos os seus dados foram excluídos com sucesso!'

            elif action == 'make_admin':
                if target_user.is_staff:
                    mensagem = f'Aviso: O usuário {target_user.username} já possui acesso de administrador.'
                else:
                    target_user.is_staff = True
                    target_user.save(update_fields=['is_staff'])
                    mensagem = f'Sucesso: Usuário {target_user.username} agora possui acesso de administrador!'

            elif action == 'remove_admin':
                if target_user == request.user:
                    mensagem = 'Erro: Você não pode remover seus próprios privilégios de administrador enquanto estiver logado.'
                elif not target_user.is_staff:
                    mensagem = f'Aviso: O usuário {target_user.username} já não possui privilégios de administrador.'
                else:
                    target_user.is_staff = False
                    target_user.save(update_fields=['is_staff'])
                    mensagem = f'Sucesso: Privilégios de administrador removidos do usuário {target_user.username}.'
        
        except User.DoesNotExist:
            mensagem = 'Erro: Usuário não encontrado!'
        except Exception as e:
            mensagem = f'Erro: Erro ao processar ação: {str(e)}'
    
    # Busca todos os usuários com suas informações
    users = User.objects.all().order_by('date_joined')
    users_data = []
    
    for user in users:
        # Conta mensagens do usuário
        message_count = Message.objects.filter(conversation__user=user).count()
        
        users_data.append({
            'user': user,
            'email': user.email,
            'message_count': message_count,
            'date_joined': user.date_joined,
        })
    
    return render(request, 'admin_panel.html', {
        'users_data': users_data,
        'mensagem': mensagem,
        'show_sidebar': True
    })
