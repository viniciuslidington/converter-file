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
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Formato não suportado" in captured.err


def test_output_exists_prints_error(mocker, tmp_path, capsys):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main.convert_media", side_effect=FileExistsError("já existe"))

    with patch("sys.argv", ["convert-file", str(src)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "já existe" in captured.err


def test_batch_mixed_groups_exits_with_error(mocker, tmp_path, capsys):
    (tmp_path / "clip.mp4").touch()
    (tmp_path / "photo.png").touch()

    def fake_detect_group(path):
        if path.endswith(".mp4"):
            return "video"
        if path.endswith(".png"):
            return "image"
        raise ValueError("Unsupported")

    mocker.patch("converter_file.main.detect_group", side_effect=fake_detect_group)

    with patch("sys.argv", ["convert-file", str(tmp_path)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "grupos de formato diferentes" in captured.err


def test_batch_no_supported_files_exits_with_error(mocker, tmp_path, capsys):
    (tmp_path / "doc.pdf").touch()

    mocker.patch("converter_file.main.detect_group", side_effect=ValueError("Unsupported"))

    with patch("sys.argv", ["convert-file", str(tmp_path / "doc.pdf"), str(tmp_path / "doc.pdf")]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Nenhum arquivo suportado encontrado" in captured.err


def test_no_args_opens_native_picker(mocker, tmp_path):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main._pick_files_native", return_value=[str(src)])
    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value=str(tmp_path / "clip.avi"))

    with patch("sys.argv", ["convert-file"]):
        main()

    mock_convert.assert_called_once_with(str(src), "avi")


def test_no_args_picker_cancelled_exits(mocker, capsys):
    mocker.patch("converter_file.main._pick_files_native", return_value=[])

    with patch("sys.argv", ["convert-file"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    assert "Nenhum arquivo selecionado" in capsys.readouterr().err
