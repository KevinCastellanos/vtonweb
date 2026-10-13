from django.apps import AppConfig


class TryonConfig(AppConfig):
    name = "tryon"
    verbose_name = "Try-on"

    def ready(self):
        from django.contrib.auth.signals import user_logged_in

        from .models import UsageEvent

        def on_login(sender, request, user, **kwargs):
            UsageEvent.objects.create(user=user, kind=UsageEvent.LOGIN, path="/login")

        user_logged_in.connect(on_login, dispatch_uid="tryon_login_event", weak=False)
