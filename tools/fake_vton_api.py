"""API falsa para probar la plataforma sin GPU: imita /v1/tryon (single-flight, tarda unos segundos)."""
import asyncio, io, os, time
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

app = FastAPI()
lock = asyncio.Lock()
KEY = os.environ.get("VTON_API_KEY", "")
DELAY = float(os.environ.get("FAKE_DELAY", "4"))

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/v1/tryon")
async def tryon(person: UploadFile = File(...), garment: UploadFile = File(...), category: str = Form("tops"),
                garment_photo_type: str = Form("flat-lay"), num_timesteps: int = Form(30),
                x_api_key: str = Header(None, alias="X-API-Key")):
    if KEY and x_api_key != KEY:
        raise HTTPException(401, "Falta una API key válida (X-API-Key).")
    async with lock:
        t = time.time(); await asyncio.sleep(DELAY)
        img = Image.open(io.BytesIO(await person.read())).convert("RGB"); img.thumbnail((768, 1024))
        buf = io.BytesIO(); img.save(buf, "PNG")
        return Response(buf.getvalue(), media_type="image/png", headers={"X-Elapsed-Seconds": f"{time.time()-t:.2f}"})
