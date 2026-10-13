from .models import UsageEvent

SKIP_PREFIXES = ("/static/", "/admin/jsi18n", "/private-media/", "/healthz")


class AccessLogMiddleware:
    """Registra cada acceso (GET de página) de usuarios autenticados para las métricas."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            user = getattr(request, "user", None)
            path = request.path
            if (
                user is not None
                and user.is_authenticated
                and request.method == "GET"
                and response.status_code < 400
                and not path.startswith(SKIP_PREFIXES)
                and not path.endswith("/estado/")
            ):
                UsageEvent.objects.create(user=user, kind=UsageEvent.PAGE, path=path[:200])
        except Exception:  # las métricas nunca deben romper la página
            pass
        return response
