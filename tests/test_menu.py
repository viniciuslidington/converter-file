import pytest
from unittest.mock import patch
from converter_file.menu import prompt_target_format


def test_valid_video_choice(capsys):
    with patch("builtins.input", return_value="1"):
        result = prompt_target_format("video")
    assert result in ["mov", "mp4", "avi", "mkv", "webm"]


def test_valid_image_choice(capsys):
    with patch("builtins.input", return_value="2"):
        result = prompt_target_format("image")
    assert result in ["jpg", "png", "webp", "gif", "bmp", "tiff"]


def test_invalid_choice_reprompts():
    # primeira resposta inválida, segunda válida
    with patch("builtins.input", side_effect=["99", "1"]):
        result = prompt_target_format("audio")
    assert result in ["mp3", "wav", "aac", "flac", "ogg"]


def test_invalid_group_raises():
    with pytest.raises(ValueError, match="Grupo inválido"):
        prompt_target_format("document")


def test_menu_shows_options(capsys):
    with patch("builtins.input", return_value="1"):
        prompt_target_format("video")
    captured = capsys.readouterr()
    assert "1." in captured.out
