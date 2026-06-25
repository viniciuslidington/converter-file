import pytest
import os
from pathlib import Path
from PIL import Image
from converter_file.convert_image import convert_image


@pytest.fixture
def tmp_png(tmp_path):
    img = Image.new("RGB", (10, 10), color="red")
    path = tmp_path / "test.png"
    img.save(path)
    return str(path)


def test_converts_png_to_jpg(tmp_png, tmp_path):
    result = convert_image(tmp_png, "jpg")
    assert result == str(tmp_path / "test.jpg")
    assert os.path.exists(result)
    img = Image.open(result)
    assert img.format == "JPEG"


def test_converts_png_to_webp(tmp_png, tmp_path):
    result = convert_image(tmp_png, "webp")
    assert result == str(tmp_path / "test.webp")
    assert os.path.exists(result)


def test_raises_if_output_exists(tmp_png, tmp_path):
    (tmp_path / "test.jpg").touch()
    with pytest.raises(FileExistsError, match="já existe"):
        convert_image(tmp_png, "jpg")


def test_raises_if_input_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert_image(str(tmp_path / "nope.png"), "jpg")
