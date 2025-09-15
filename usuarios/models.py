from django.db import models
from django.contrib.auth.models import User

# Modelo para armazenar o perfil do usuário
class PerfilUsuario(models.Model):
    PERFIS_INVESTIDOR = [
        ('CONSERVADOR', 'Conservador'),
        ('MODERADO', 'Moderado'),
        ('AGRESSIVO', 'Agressivo'),
        ('NAO_DEFINIDO', 'Não Definido'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    perfil_investidor = models.CharField(max_length=20, choices=PERFIS_INVESTIDOR, default='NAO_DEFINIDO')
    questionario_completo = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} - {self.perfil_investidor}'