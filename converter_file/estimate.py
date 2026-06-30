import io
import json
import subprocess
from pathlib import Path
from typing import Iterable

from PIL import Image

from converter_file.detect import SUPPORTED_FORMATS

AUDIO_BITRATES: dict[str, int] = {
    "mp3": 192_000,
    "wav": 1_411_200,
    "m4a": 192_000,
    "aac": 192_000,
    "flac": 700_000,
    "ogg": 192_000,
    "opus": 128_000,
}

VIDEO_BITRATES: dict[str, int] = {
    "mov": 4_000_000,
    "mp4": 4_000_000,
    "avi": 5_000_000,
    "mkv": 4_000_000,
    "webm": 3_000_000,
}

VIDEO_SIZE_FACTORS: dict[str, float] = {
    "mov": 1.0,
    "mp4": 1.0,
    "avi": 1.25,
    "mkv": 1.0,
    "webm": 0.75,
}

IMAGE_FORMATS: dict[str, str] = {
    "jpg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
}


def estimate_output_size_labels(
    input_paths: Iterable[str],
    target_formats: Iterable[str],
    source_group: str,
) -> dict[str, str]:
    paths = list(input_paths)
    if not paths:
        return {}

    estimates: dict[str, str] = {}
    for target_format in target_formats:
        size = estimate_output_size(paths, target_format, source_group)
        if size is not None:
            estimates[target_format] = f"~{format_file_size(size)}"
    return estimates


def estimate_output_size(paths: Iterable[str], target_format: str, source_group: str) -> int | None:
    sizes = [
        estimate_single_output_size(path, target_format, source_group)
        for path in paths
    ]
    known_sizes = [size for size in sizes if size is not None]
    if len(known_sizes) != len(sizes):
        return None
    return sum(known_sizes)


def estimate_single_output_size(path: str, target_format: str, source_group: str) -> int | None:
    if source_group == "image":
        return _estimate_image_size(path, target_format)
    if source_group in {"video", "audio"}:
        return _estimate_media_size(path, target_format)
    return None


def format_file_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size_bytes} B"


def _estimate_image_size(path: str, target_format: str) -> int | None:
    image_format = IMAGE_FORMATS.get(target_format)
    if image_format is None:
        return None

    try:
        with Image.open(path) as image:
            converted = image
            if image_format == "JPEG" and image.mode not in ("RGB", "L"):
                converted = image.convert("RGB")

            output = io.BytesIO()
            converted.save(output, format=image_format)
            return output.tell()
    except OSError:
        return None


def _estimate_media_size(path: str, target_format: str) -> int | None:
    metadata = _probe_media(path)
    if metadata is None:
        return None

    duration = metadata.get("duration")
    if not duration or duration <= 0:
        return None

    if target_format in SUPPORTED_FORMATS["audio"]:
        bitrate = AUDIO_BITRATES.get(target_format)
    else:
        bitrate = _estimate_video_bitrate(metadata, target_format)

    if bitrate is None:
        return None

    return int(duration * bitrate / 8)


def _estimate_video_bitrate(metadata: dict[str, float | int | None], target_format: str) -> int | None:
    bitrate = metadata.get("bit_rate")
    if bitrate is None:
        bitrate = VIDEO_BITRATES.get(target_format)
    if bitrate is None:
        return None

    factor = VIDEO_SIZE_FACTORS.get(target_format, 1.0)
    return int(bitrate * factor)


def _probe_media(path: str) -> dict[str, float | int | None] | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,bit_rate,size",
                "-of",
                "json",
                str(Path(path)),
            ],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    media_format = data.get("format", {})
    return {
        "duration": _parse_float(media_format.get("duration")),
        "bit_rate": _parse_int(media_format.get("bit_rate")),
        "size": _parse_int(media_format.get("size")),
    }


def _parse_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
