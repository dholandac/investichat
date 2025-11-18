from django.contrib import admin
from django.urls import path, include
from usuarios import views as usuarios_views

urlpatterns = [
    path('', usuarios_views.landing, name='landing'),
    path('admin/', admin.site.urls),
    path('auth/', include('usuarios.urls')),
    path('chatbot/', include('chatbot.urls'))
]
