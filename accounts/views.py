from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from tryon.models import UsageEvent

from .forms import ProfileForm, RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("studio")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        UsageEvent.objects.create(user=user, kind=UsageEvent.REGISTER, path="/cuenta/registro/")
        login(request, user)  # dispara también el evento de login
        messages.success(request, "¡Cuenta creada! Ya puedes probarte prendas.")
        return redirect("studio")
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Perfil actualizado.")
        return redirect("profile")
    return render(request, "registration/profile.html", {"form": form})


class PasswordChange(PasswordChangeView):
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        messages.success(self.request, "Contraseña cambiada correctamente.")
        return super().form_valid(form)
