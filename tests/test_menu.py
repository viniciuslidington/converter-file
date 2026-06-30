import pytest
from unittest.mock import patch
from converter_file.menu import ConversionCancelled, prompt_target_format


def test_valid_video_choice(capsys):
    with patch("builtins.input", return_value="1"):
        result = prompt_target_format("video")
    assert result in ["mov", "mp4", "avi", "mkv", "webm", "mp3", "wav", "m4a", "aac", "flac", "ogg", "opus"]


def test_number_menu_shows_estimated_size(mocker, capsys):
    mocker.patch(
        "converter_file.menu.estimate_output_size_labels",
        return_value={"mp3": "~2.3 MB"},
    )

    with patch("builtins.input", return_value="1"):
        prompt_target_format("audio", ["song.wav"])

    assert ".mp3 (~2.3 MB estimado)" in capsys.readouterr().out


def test_interactive_menu_uses_questionary(mocker):
    mocker.patch("converter_file.menu._supports_arrow_menu", return_value=True)
    mocker.patch("converter_file.menu._prompt_with_questionary", return_value="wav")

    result = prompt_target_format("audio")

    assert result == "wav"


def test_interactive_menu_falls_back_to_manual_arrows(mocker):
    mocker.patch("converter_file.menu._supports_arrow_menu", return_value=True)
    mocker.patch("converter_file.menu._prompt_with_questionary", side_effect=ImportError)
    mocker.patch("converter_file.menu._read_key", side_effect=["down", "enter"])

    result = prompt_target_format("audio")

    assert result == "wav"


def test_interactive_menu_can_cancel(mocker):
    mocker.patch("converter_file.menu._supports_arrow_menu", return_value=True)
    mocker.patch("converter_file.menu._prompt_with_questionary", side_effect=ConversionCancelled)

    with pytest.raises(ConversionCancelled):
        prompt_target_format("audio")


def test_number_menu_can_cancel():
    with patch("builtins.input", return_value="0"):
        with pytest.raises(ConversionCancelled):
            prompt_target_format("audio")


def test_manual_arrow_menu_can_cancel(mocker):
    mocker.patch("converter_file.menu._supports_arrow_menu", return_value=True)
    mocker.patch("converter_file.menu._prompt_with_questionary", side_effect=ImportError)
    mocker.patch("converter_file.menu._read_key", side_effect=["up", "enter"])

    with pytest.raises(ConversionCancelled):
        prompt_target_format("audio")


def test_video_menu_accepts_audio_target(capsys):
    with patch("builtins.input", return_value="6"):
        result = prompt_target_format("video")
    assert result == "mp3"


def test_valid_image_choice(capsys):
    with patch("builtins.input", return_value="2"):
        result = prompt_target_format("image")
    assert result in ["jpg", "png", "webp", "gif", "bmp", "tiff"]


def test_invalid_choice_reprompts():
    # primeira resposta inválida, segunda válida
    with patch("builtins.input", side_effect=["99", "1"]):
        result = prompt_target_format("audio")
    assert result in ["mp3", "wav", "m4a", "aac", "flac", "ogg", "opus"]


def test_invalid_group_raises():
    with pytest.raises(ValueError, match="Grupo inválido"):
        prompt_target_format("unknown")


def test_menu_shows_options(capsys):
    with patch("builtins.input", return_value="1"):
        prompt_target_format("video")
    captured = capsys.readouterr()
    assert "1." in captured.out
