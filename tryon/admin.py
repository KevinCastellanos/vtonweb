from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Avg, Count, Max, Q
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone

from .models import TryOnJob, UsageEvent

User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class UserStatsAdmin(UserAdmin):
    list_display = ("username", "email", "date_joined", "last_login", "n_jobs", "n_logins", "n_access", "is_staff")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _jobs=Count("jobs", distinct=True),
            _logins=Count("usageevent", filter=Q(usageevent__kind="login"), distinct=True),
            _access=Count("usageevent", filter=Q(usageevent__kind="page"), distinct=True),
        )

    @admin.display(description="Uso de API", ordering="_jobs")
    def n_jobs(self, obj):
        return obj._jobs

    @admin.display(description="Inicios de sesión", ordering="_logins")
    def n_logins(self, obj):
        return obj._logins

    @admin.display(description="Accesos", ordering="_access")
    def n_access(self, obj):
        return obj._access


@admin.register(TryOnJob)
class TryOnJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "category", "attempts", "api_seconds", "created_at", "finished_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("user__username", "error")
    readonly_fields = ("created_at", "started_at", "finished_at")


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "kind", "path")
    list_filter = ("kind", "created_at")
    search_fields = ("user__username", "path")
    date_hierarchy = "created_at"


def dashboard_context(days=14):
    now = timezone.now()
    since = now - timedelta(days=days)
    day7 = now - timedelta(days=7)
    jobs = TryOnJob.objects
    done = jobs.filter(status=TryOnJob.DONE)

    def series(qs, field):
        rows = {r["d"]: r["n"] for r in qs.annotate(d=TruncDate(field)).values("d").annotate(n=Count("id"))}
        labels, values = [], []
        for i in range(days, -1, -1):
            d = (now - timedelta(days=i)).date()
            labels.append(d.strftime("%d/%m"))
            values.append(rows.get(d, 0))
        return labels, values

    jl, jv = series(jobs.filter(created_at__gte=since), "created_at")
    _, lv = series(UsageEvent.objects.filter(kind="login", created_at__gte=since), "created_at")
    _, rv = series(User.objects.filter(date_joined__gte=since), "date_joined")
    hours = {
        r["h"]: r["n"]
        for r in UsageEvent.objects.filter(created_at__gte=since, kind__in=["page", "job"])
        .annotate(h=ExtractHour("created_at"))
        .values("h")
        .annotate(n=Count("id"))
    }
    status = {r["status"]: r["n"] for r in jobs.values("status").annotate(n=Count("id"))}
    wait = [j.wait_seconds for j in jobs.exclude(started_at=None).order_by("-id")[:50] if j.wait_seconds is not None]
    active_ids = (
        UsageEvent.objects.filter(created_at__gte=day7, user__isnull=False).values("user").distinct().count()
    )
    return {
        "dash_days": days,
        "kpis": [
            ("Usuarios registrados", User.objects.count(), "people"),
            ("Nuevos (7 días)", User.objects.filter(date_joined__gte=day7).count(), "person-plus"),
            ("Usuarios activos (7 días)", active_ids, "activity"),
            ("Inicios de sesión (24 h)", UsageEvent.objects.filter(kind="login", created_at__gte=now - timedelta(hours=24)).count(), "box-arrow-in-right"),
            ("Llamadas a la API (total)", jobs.count(), "cpu"),
            ("Completadas", status.get("done", 0), "check2-circle"),
            ("Con error", status.get("error", 0), "exclamation-triangle"),
            ("En cola ahora", status.get("queued", 0) + status.get("processing", 0), "hourglass-split"),
            ("Tiempo medio de IA (s)", round(done.aggregate(a=Avg("api_seconds"))["a"] or 0, 1), "stopwatch"),
            ("Espera media en cola (s)", round(sum(wait) / len(wait), 1) if wait else 0, "clock-history"),
        ],
        "chart": {
            "days": jl,
            "jobs": jv,
            "logins": lv,
            "regs": rv,
            "hours": [hours.get(h, 0) for h in range(24)],
            "status": [status.get(k, 0) for k in ("done", "error", "queued", "processing")],
        },
        "top_users": list(
            User.objects.annotate(n=Count("jobs"), last=Max("jobs__created_at"))
            .filter(n__gt=0)
            .order_by("-n")[:8]
            .values("username", "n", "last")
        ),
        "recent_events": UsageEvent.objects.select_related("user")[:10],
    }


_orig_index = admin.site.index


def _index(request, extra_context=None):
    extra = dict(extra_context or {})
    extra.update(dashboard_context())
    return _orig_index(request, extra)


admin.site.index = _index
