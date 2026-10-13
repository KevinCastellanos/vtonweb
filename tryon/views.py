from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import connection
from django.db.models import Avg
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import TryOnForm
from .models import TryOnJob, UsageEvent
from .services import normalize_image


def healthz(request):
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


def home(request):
    if request.user.is_authenticated:
        return redirect("studio")
    return render(request, "home.html")


def _avg_seconds():
    avg = TryOnJob.objects.filter(status=TryOnJob.DONE).order_by("-id")[:20].values_list("api_seconds", flat=True)
    vals = [v for v in avg if v]
    return round(sum(vals) / len(vals), 1) if vals else 25.0


@login_required
def studio(request):
    form = TryOnForm()
    if request.method == "POST":
        form = TryOnForm(request.POST, request.FILES)
        active = TryOnJob.objects.filter(
            user=request.user, status__in=[TryOnJob.QUEUED, TryOnJob.PROCESSING]
        ).count()
        if active >= settings.MAX_ACTIVE_JOBS_PER_USER:
            return JsonResponse(
                {"ok": False, "error": f"Ya tienes {active} solicitudes en curso. Espera a que terminen."},
                status=429,
            )
        if not form.is_valid():
            errs = "; ".join(e for errors in form.errors.values() for e in errors)
            return JsonResponse({"ok": False, "error": errs}, status=400)
        try:
            person = normalize_image(form.cleaned_data["person"])
            garment = normalize_image(form.cleaned_data["garment"])
        except ValueError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        job = TryOnJob(
            user=request.user,
            category=form.cleaned_data["category"],
            garment_photo_type=form.cleaned_data["garment_photo_type"],
            num_timesteps=settings.VTON_STEPS,
        )
        job.person_image.save("person.jpg", ContentFile(person), save=False)
        job.garment_image.save("garment.jpg", ContentFile(garment), save=False)
        job.save()
        UsageEvent.objects.create(user=request.user, kind=UsageEvent.JOB, path=f"/jobs/{job.pk}/")
        return JsonResponse({"ok": True, "id": job.pk, "url": f"/trabajos/{job.pk}/"})
    return render(request, "studio.html", {"form": form, "max_mb": settings.MAX_UPLOAD_MB})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(TryOnJob, pk=pk, user=request.user)
    return render(request, "job_detail.html", {"job": job})


def _status_payload(job):
    return {
        "id": job.pk,
        "status": job.status,
        "status_label": job.get_status_display(),
        "position": job.queue_position(),
        "eta": round(_avg_seconds() * (job.queue_position() + 1)),
        "avg": _avg_seconds(),
        "error": job.error,
        "api_seconds": job.api_seconds,
        "result": f"/trabajos/{job.pk}/imagen/result/" if job.status == TryOnJob.DONE else None,
    }


@login_required
def job_status(request, pk):
    job = get_object_or_404(TryOnJob, pk=pk, user=request.user)
    return JsonResponse(_status_payload(job))


@login_required
def job_media(request, pk, kind):
    job = get_object_or_404(TryOnJob, pk=pk, user=request.user)
    field = {"person": job.person_image, "garment": job.garment_image, "result": job.result_image}.get(kind)
    if not field:
        raise Http404
    return FileResponse(field.open("rb"))


@login_required
def history(request):
    jobs = TryOnJob.objects.filter(user=request.user)[:60]
    return render(request, "history.html", {"jobs": jobs})


@login_required
@require_POST
def job_delete(request, pk):
    job = get_object_or_404(TryOnJob, pk=pk, user=request.user)
    for f in (job.person_image, job.garment_image, job.result_image):
        if f:
            f.delete(save=False)
    job.delete()
    messages.success(request, "Solicitud eliminada.")
    return redirect("history")
