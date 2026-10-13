from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("registro/", views.register, name="register"),
    path("entrar/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("perfil/", views.profile, name="profile"),
    path("contrasena/", views.PasswordChange.as_view(), name="password_change"),
]
