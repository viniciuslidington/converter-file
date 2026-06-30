import pytest
from converter_file.detect import detect_group, SUPPORTED_FORMATS


def test_video_extensions():
    for ext in ["mov", "mp4", "avi", "mkv", "webm"]:
        assert detect_group(f"file.{ext}") == "video"


def test_audio_extensions():
    for ext in ["mp3", "wav", "m4a", "aac", "flac", "ogg", "opus"]:
        assert detect_group(f"file.{ext}") == "audio"


def test_image_extensions():
    for ext in ["jpg", "png", "webp", "gif", "bmp", "tiff"]:
        assert detect_group(f"file.{ext}") == "image"


def test_pdf_extensions():
    assert detect_group("file.pdf") == "pdf"


def test_document_extensions():
    for ext in ["docx", "pptx", "xlsx", "odt", "rtf", "txt", "md", "html"]:
        assert detect_group(f"file.{ext}") == "document"


def test_uppercase_extension():
    assert detect_group("file.MP4") == "video"


def test_unsupported_raises():
    with pytest.raises(ValueError, match="Formato não suportado"):
        detect_group("file.csv")


def test_supported_formats_keys():
    assert set(SUPPORTED_FORMATS.keys()) == {"video", "audio", "image", "pdf", "document"}
