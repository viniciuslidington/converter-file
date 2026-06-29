SUPPORTED_FORMATS: dict[str, list[str]] = {
    "video": ["mov", "mp4", "avi", "mkv", "webm"],
    "audio": ["mp3", "wav", "aac", "flac", "ogg"],
    "image": ["jpg", "png", "webp", "gif", "bmp", "tiff"],
}

TARGET_FORMATS: dict[str, list[str]] = {
    **SUPPORTED_FORMATS,
    "video": SUPPORTED_FORMATS["video"] + SUPPORTED_FORMATS["audio"],
}

_EXT_TO_GROUP: dict[str, str] = {
    ext: group
    for group, exts in SUPPORTED_FORMATS.items()
    for ext in exts
}


def detect_group(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower()
    group = _EXT_TO_GROUP.get(ext)
    if group is None:
        raise ValueError(f"Formato não suportado: .{ext}")
    return group
