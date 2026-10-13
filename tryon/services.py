"""Cliente de la API vton-api (una sola petición a la vez: single-flight)."""
import io

import requests
from django.conf import settings
from PIL import Image


class RetryableError(Exception):
    """La API está saturada o no disponible: se reintenta más tarde."""


class PermanentError(Exception):
    """La API rechazó la petición: no tiene sentido reintentar."""


def normalize_image(uploaded, max_side=2048):
    """Valida que sea una imagen real y la reduce; devuelve bytes PNG/JPEG."""
    try:
        img = Image.open(uploaded)
        img.verify()
        uploaded.seek(0)
        img = Image.open(uploaded).convert("RGB")
    except Exception as exc:
        raise ValueError("El archivo no es una imagen válida.") from exc
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def call_tryon(person_bytes, garment_bytes, category, photo_type, steps):
    url = f"{settings.VTON_API_URL}/v1/tryon"
    headers = {"X-API-Key": settings.VTON_API_KEY} if settings.VTON_API_KEY else {}
    try:
        resp = requests.post(
            url,
            params={"raw": "true"},
            headers=headers,
            files={
                "person": ("person.jpg", person_bytes, "image/jpeg"),
                "garment": ("garment.jpg", garment_bytes, "image/jpeg"),
            },
            data={"category": category, "garment_photo_type": photo_type, "num_timesteps": steps},
            timeout=settings.VTON_API_TIMEOUT,
        )
    except (requests.ConnectionError, requests.Timeout) as exc:
        raise RetryableError(f"No se pudo contactar la API: {type(exc).__name__}") from exc

    if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
        elapsed = float(resp.headers.get("X-Elapsed-Seconds", "0") or 0)
        return resp.content, elapsed
    if resp.status_code in (502, 503, 504):
        raise RetryableError(f"API ocupada ({resp.status_code})")
    try:
        detail = resp.json().get("detail", resp.text[:200])
    except Exception:
        detail = resp.text[:200]
    if resp.status_code in (401, 403):
        raise PermanentError("La plataforma no está autorizada en la API (revisa VTON_API_KEY).")
    raise PermanentError(f"La API respondió {resp.status_code}: {detail}")
