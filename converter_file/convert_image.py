import os
from pathlib import Path
from PIL import Image

_PILLOW_FORMAT: dict[str, str] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
}


def convert_image(input_path: str, target_format: str) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    dst = src.with_suffix(f".{target_format}")
    if dst.exists():
        raise FileExistsError(f"Arquivo de saída já existe: {dst}")

    pillow_fmt = _PILLOW_FORMAT.get(target_format.lower())
    if pillow_fmt is None:
        raise ValueError(f"Formato de imagem não suportado: {target_format}")

    img = Image.open(src)
    if pillow_fmt == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(dst, format=pillow_fmt)
    return str(dst)
