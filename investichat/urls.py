from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('/chatbot/', permanent=False)),
    path('admin/', admin.site.urls),
    path('auth/', include('usuarios.urls')),
    path('chatbot/', include('chatbot.urls'))
]
