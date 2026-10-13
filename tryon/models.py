import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def upload_to(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    now = timezone.now()
    return f"jobs/{now:%Y/%m}/{uuid.uuid4().hex}.{ext}"


class UsageEvent(models.Model):
    LOGIN, REGISTER, PAGE, JOB = "login", "register", "page", "job"
    KINDS = [
        (LOGIN, "Inicio de sesión"),
        (REGISTER, "Registro"),
        (PAGE, "Acceso a página"),
        (JOB, "Solicitud de try-on"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    kind = models.CharField(max_length=12, choices=KINDS, db_index=True)
    path = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "evento de uso"
        verbose_name_plural = "eventos de uso"

    def __str__(self):
        return f"{self.kind} · {self.user} · {self.created_at:%Y-%m-%d %H:%M}"


class TryOnJob(models.Model):
    QUEUED, PROCESSING, DONE, ERROR = "queued", "processing", "done", "error"
    STATUSES = [(QUEUED, "En cola"), (PROCESSING, "Procesando"), (DONE, "Listo"), (ERROR, "Error")]
    CATEGORIES = [("tops", "Parte superior"), ("bottoms", "Parte inferior"), ("one-pieces", "Prenda completa")]
    PHOTO_TYPES = [("flat-lay", "Prenda sobre fondo plano"), ("model", "Prenda puesta en modelo")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs")
    person_image = models.FileField(upload_to=upload_to)
    garment_image = models.FileField(upload_to=upload_to)
    result_image = models.FileField(upload_to=upload_to, blank=True)
    category = models.CharField(max_length=12, choices=CATEGORIES, default="tops")
    garment_photo_type = models.CharField(max_length=10, choices=PHOTO_TYPES, default="flat-lay")
    num_timesteps = models.PositiveSmallIntegerField(default=30)
    status = models.CharField(max_length=12, choices=STATUSES, default=QUEUED, db_index=True)
    error = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    not_before = models.DateTimeField(default=timezone.now)
    api_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "solicitud de try-on"
        verbose_name_plural = "solicitudes de try-on"

    def __str__(self):
        return f"#{self.pk} {self.user} {self.status}"

    @property
    def wait_seconds(self):
        if self.started_at:
            return (self.started_at - self.created_at).total_seconds()
        return None

    def queue_position(self):
        """0 = es el siguiente (o ya se procesa). Cuenta los trabajos anteriores en cola."""
        if self.status != self.QUEUED:
            return 0
        ahead = TryOnJob.objects.filter(status=self.QUEUED, id__lt=self.id).count()
        busy = TryOnJob.objects.filter(status=self.PROCESSING).exists()
        return ahead + (1 if busy else 0)
