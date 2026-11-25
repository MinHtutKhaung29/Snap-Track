import io
import os
import uuid
from datetime import datetime, timedelta, timezone

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPLOAD_ROOT = os.path.join(ROOT, "uploads")
MAX_BYTES = 5 * 1024 * 1024
CHUNK_SIZE = 64 * 1024
MAX_SIDE = 1600
JST = timezone(timedelta(hours=9))


class UploadError(Exception):
    pass


def read_bounded(stream, max_bytes=MAX_BYTES):
    chunks = []
    total = 0
    limit = max_bytes + 1
    while total < limit:
        chunk = stream.read(min(CHUNK_SIZE, limit - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    return b"".join(chunks)


def save_receipt_image(data):
    if not data:
        raise UploadError("empty")
    if len(data) > MAX_BYTES:
        raise UploadError("too_large")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception:
        raise UploadError("not_an_image")
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    width, height = image.size
    if width < 200 or height < 200:
        raise UploadError("too_small")
    scale = MAX_SIDE / float(max(width, height))
    if scale < 1:
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    now = datetime.now(JST)
    folder = os.path.join(UPLOAD_ROOT, now.strftime("%Y"), now.strftime("%m"))
    os.makedirs(folder, exist_ok=True)
    name = uuid.uuid4().hex + ".jpg"
    path = os.path.join(folder, name)
    clean = Image.new("RGB", image.size, "white")
    clean.paste(image, (0, 0))
    clean.save(path, "JPEG", quality=85, optimize=True, exif=b"")
    relative = os.path.relpath(path, UPLOAD_ROOT).replace(os.sep, "/")
    return relative, os.path.getsize(path), clean.size


def absolute_path(relative):
    safe = os.path.normpath(relative).replace("\\", "/")
    if safe.startswith("..") or os.path.isabs(safe):
        raise UploadError("bad_path")
    return os.path.join(UPLOAD_ROOT, safe)
