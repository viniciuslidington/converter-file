import pytest
from unittest.mock import patch
from converter_file.main import _convert_single, main
from converter_file.menu import ConversionCancelled


def test_convert_single_prints_output_path(mocker, tmp_path, capsys):
    src = tmp_path / "clip.mp4"
    src.touch()
    out = tmp_path / "clip.avi"

    def fake_convert_media(file_path, target_format, output_path=None):
        out.write_bytes(b"x" * 1536)
        return str(out)

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.convert_media", side_effect=fake_convert_media)

    assert _convert_single(str(src), "avi", str(out)) is True

    captured = capsys.readouterr()
    assert captured.out == f"Convertido: {out}\n"


def test_single_file_conversion(mocker, tmp_path):
    src = tmp_path / "clip.mp4"
    src.touch()
    out = str(tmp_path / "clip.avi")

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main._pick_save_file", return_value=out)
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value=out)

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    mock_convert.assert_called_once_with(str(src), "avi", out)


def test_single_image_conversion(mocker, tmp_path):
    src = tmp_path / "photo.png"
    src.touch()
    out = str(tmp_path / "photo.jpg")

    mocker.patch("converter_file.main.detect_group", return_value="image")
    mocker.patch("converter_file.main.prompt_target_format", return_value="jpg")
    mocker.patch("converter_file.main._pick_save_file", return_value=out)
    mock_convert = mocker.patch("converter_file.main.convert_image", return_value=out)

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    mock_convert.assert_called_once_with(str(src), "jpg", out)


def test_single_file_save_dialog_cancelled(mocker, tmp_path, capsys):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main._pick_save_file", return_value=None)

    with patch("sys.argv", ["convert-file", str(src)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    assert "Destino não selecionado" in capsys.readouterr().err


def test_single_file_format_selection_cancelled(mocker, tmp_path, capsys):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", side_effect=ConversionCancelled)
    pick_save = mocker.patch("converter_file.main._pick_save_file")

    with patch("sys.argv", ["convert-file", str(src)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    assert "Conversão cancelada" in capsys.readouterr().out
    pick_save.assert_not_called()


def test_batch_directory(mocker, tmp_path):
    (tmp_path / "a.mp4").touch()
    (tmp_path / "b.mp4").touch()
    save_folder = str(tmp_path / "output")

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main._pick_save_folder", return_value=save_folder)
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value="out.avi")

    with patch("sys.argv", ["convert-file", str(tmp_path)]):
        main()

    assert mock_convert.call_count == 2


def test_batch_folder_dialog_cancelled(mocker, tmp_path, capsys):
    (tmp_path / "a.mp4").touch()
    (tmp_path / "b.mp4").touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main._pick_save_folder", return_value=None)

    with patch("sys.argv", ["convert-file", str(tmp_path)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    assert "Destino não selecionado" in capsys.readouterr().err


def test_batch_format_selection_cancelled(mocker, tmp_path, capsys):
    (tmp_path / "a.mp4").touch()
    (tmp_path / "b.mp4").touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", side_effect=ConversionCancelled)
    pick_folder = mocker.patch("converter_file.main._pick_save_folder")

    with patch("sys.argv", ["convert-file", str(tmp_path)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    assert "Conversão cancelada" in capsys.readouterr().out
    pick_folder.assert_not_called()


def test_unsupported_format_prints_error(mocker, tmp_path, capsys):
    src = tmp_path / "doc.pdf"
    src.touch()

    mocker.patch("converter_file.main.detect_group", side_effect=ValueError("Formato não suportado: .pdf"))

    with patch("sys.argv", ["convert-file", str(src)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    assert "Formato não suportado" in capsys.readouterr().err


def test_output_exists_prints_error(mocker, tmp_path, capsys):
    src = tmp_path / "clip.mp4"
    src.touch()
    out = str(tmp_path / "clip.avi")

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main._pick_save_file", return_value=out)
    mocker.patch("converter_file.main.convert_media", side_effect=FileExistsError("já existe"))

    with patch("sys.argv", ["convert-file", str(src)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    assert "já existe" in capsys.readouterr().err


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
    assert "grupos de formato diferentes" in capsys.readouterr().err


def test_batch_no_supported_files_exits_with_error(mocker, tmp_path, capsys):
    (tmp_path / "doc.pdf").touch()

    mocker.patch("converter_file.main.detect_group", side_effect=ValueError("Unsupported"))

    with patch("sys.argv", ["convert-file", str(tmp_path / "doc.pdf"), str(tmp_path / "doc.pdf")]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    assert "Nenhum arquivo suportado encontrado" in capsys.readouterr().err


def test_no_args_opens_native_picker(mocker, tmp_path):
    src = tmp_path / "clip.mp4"
    src.touch()
    out = str(tmp_path / "clip.avi")

    mocker.patch("converter_file.main._pick_files", return_value=[str(src)])
    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main._pick_save_file", return_value=out)
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value=out)

    with patch("sys.argv", ["convert-file"]):
        main()

    mock_convert.assert_called_once_with(str(src), "avi", out)


def test_no_args_picker_cancelled_exits(mocker, capsys):
    mocker.patch("converter_file.main._pick_files", return_value=[])

    with patch("sys.argv", ["convert-file"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    assert "Nenhum arquivo selecionado" in capsys.readouterr().err
