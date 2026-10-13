"""Worker de la cola: toma trabajos 'queued' de uno en uno y llama a vton-api."""
import logging
import time
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import OperationalError, close_old_connections
from django.core.management.base import BaseCommand
from django.utils import timezone

from tryon.models import TryOnJob
from tryon.services import PermanentError, RetryableError, call_tryon

log = logging.getLogger("worker")


def claim():
    """Reserva el trabajo más antiguo de forma atómica (válido con SQLite y PostgreSQL)."""
    now = timezone.now()
    for job in TryOnJob.objects.filter(status=TryOnJob.QUEUED, not_before__lte=now).order_by("id")[:5]:
        updated = TryOnJob.objects.filter(pk=job.pk, status=TryOnJob.QUEUED).update(
            status=TryOnJob.PROCESSING, started_at=now, attempts=job.attempts + 1
        )
        if updated:
            job.refresh_from_db()
            return job
    return None


def process(job):
    try:
        with job.person_image.open("rb") as p, job.garment_image.open("rb") as g:
            png, elapsed = call_tryon(p.read(), g.read(), job.category, job.garment_photo_type, job.num_timesteps)
        job.result_image.save(f"result_{job.pk}.png", ContentFile(png), save=False)
        job.status, job.api_seconds, job.error = TryOnJob.DONE, elapsed, ""
        job.finished_at = timezone.now()
        log.info("job %s listo en %.1fs", job.pk, elapsed)
    except RetryableError as exc:
        if job.attempts < settings.JOB_MAX_ATTEMPTS:
            job.status = TryOnJob.QUEUED
            job.not_before = timezone.now() + timedelta(seconds=15 * job.attempts)
            job.error = f"Reintentando ({job.attempts}/{settings.JOB_MAX_ATTEMPTS}): {exc}"
            log.warning("job %s reintento: %s", job.pk, exc)
        else:
            job.status, job.error, job.finished_at = TryOnJob.ERROR, f"{exc}. Intenta de nuevo más tarde.", timezone.now()
    except PermanentError as exc:
        job.status, job.error, job.finished_at = TryOnJob.ERROR, str(exc), timezone.now()
    except Exception as exc:  # noqa: BLE001
        log.exception("job %s falló", job.pk)
        job.status, job.error, job.finished_at = TryOnJob.ERROR, f"Error inesperado: {exc}", timezone.now()
    job.save()


class Command(BaseCommand):
    help = "Procesa la cola de try-on (un trabajo a la vez)."

    def handle(self, *args, **opts):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
        # Si el worker murió a medias, esos trabajos vuelven a la cola.
        stuck = TryOnJob.objects.filter(status=TryOnJob.PROCESSING).update(status=TryOnJob.QUEUED)
        if stuck:
            log.warning("recuperados %s trabajos en 'processing'", stuck)
        log.info("worker listo; API=%s", settings.VTON_API_URL)
        while True:
            try:
                close_old_connections()
                job = claim()
                if job is None:
                    time.sleep(settings.WORKER_POLL_SECONDS)
                    continue
                log.info("job %s iniciado (intento %s)", job.pk, job.attempts)
                process(job)
            except OperationalError as exc:
                log.error("BD no disponible: %s", exc)
                time.sleep(5)
