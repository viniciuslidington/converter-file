SUPPORTED_FORMATS: dict[str, list[str]] = {
    "video": ["mov", "mp4", "avi", "mkv", "webm"],
    "audio": ["mp3", "wav", "m4a", "aac", "flac", "ogg", "opus"],
    "image": ["jpg", "png", "webp", "gif", "bmp", "tiff"],
    "pdf": ["pdf"],
    "document": ["docx", "pptx", "xlsx", "odt", "rtf", "txt", "md", "html"],
}

TARGET_FORMATS: dict[str, list[str]] = {
    **SUPPORTED_FORMATS,
    "video": SUPPORTED_FORMATS["video"] + SUPPORTED_FORMATS["audio"],
    "pdf": ["pdf", "docx", "txt", "md", "html", "odt", "rtf", "png", "jpg", "webp"],
    "document": ["pdf", "docx", "txt", "md", "html", "odt", "rtf", "png", "jpg", "webp"],
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
