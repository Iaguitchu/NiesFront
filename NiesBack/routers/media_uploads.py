import os, uuid, imghdr, shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent.parent

# Defaults para DEV: app/media  |  Em produção MEDIA_DIR=/data/media
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", str((BASE_DIR / "media").resolve())))
MEDIA_URL = os.getenv("MEDIA_URL", "/media")

router = APIRouter(prefix="", tags=["media"])

ALLOWED_KINDS = {
    "jpeg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "webp": ".webp",
}

@router.on_event("startup")
def _ensure_media():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    # 1) checagem rápida por content-type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo não é imagem.")

    # 2) grava temporário
    tmp_name = f"{uuid.uuid4().hex}.bin"
    tmp_path = MEDIA_DIR / tmp_name
    with tmp_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # 3) detecta tipo real
    kind = imghdr.what(tmp_path)  # 'jpeg', 'png', 'gif', 'webp', ...
    ext = ALLOWED_KINDS.get(kind)
    if not ext:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Tipo de imagem não suportado (use jpg/png/gif/webp).")

    # 4) renomeia pra chave final estável
    final_name = f"{uuid.uuid4().hex}{ext}"
    final_path = MEDIA_DIR / final_name
    tmp_path.rename(final_path)

    return {"key": final_name, "url": f"{MEDIA_URL}/{final_name}"}

def mount_media(app: FastAPI):
    # cria a pasta antes do mount
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(MEDIA_URL, StaticFiles(directory=str(MEDIA_DIR)), name="media")
