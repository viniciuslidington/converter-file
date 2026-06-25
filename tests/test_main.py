# tests/test_main.py
import pytest
from unittest.mock import patch, call
from converter_file.main import main


def test_single_file_conversion(mocker, tmp_path):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value=str(tmp_path / "clip.avi"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    mock_convert.assert_called_once_with(str(src), "avi")


def test_single_image_conversion(mocker, tmp_path):
    src = tmp_path / "photo.png"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="image")
    mocker.patch("converter_file.main.prompt_target_format", return_value="jpg")
    mock_convert = mocker.patch("converter_file.main.convert_image", return_value=str(tmp_path / "photo.jpg"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    mock_convert.assert_called_once_with(str(src), "jpg")


def test_batch_directory(mocker, tmp_path):
    (tmp_path / "a.mp4").touch()
    (tmp_path / "b.mp4").touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value="out.avi")

    with patch("sys.argv", ["convert-file", str(tmp_path)]):
        main()

    assert mock_convert.call_count == 2


def test_unsupported_format_prints_error(mocker, tmp_path, capsys):
    src = tmp_path / "doc.pdf"
    src.touch()

    mocker.patch("converter_file.main.detect_group", side_effect=ValueError("Formato não suportado: .pdf"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    captured = capsys.readouterr()
    assert "Formato não suportado" in captured.err


def test_output_exists_prints_error(mocker, tmp_path, capsys):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main.convert_media", side_effect=FileExistsError("já existe"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    captured = capsys.readouterr()
    assert "já existe" in captured.err
