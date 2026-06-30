import json

import pytest

from converter_file import api


def test_inspect_file_returns_detected_metadata(tmp_path):
    src = tmp_path / "song.mp3"
    src.write_bytes(b"abc")

    result = api.inspect_file(str(src))

    assert result["path"] == str(src)
    assert result["name"] == "song.mp3"
    assert result["extension"] == "mp3"
    assert result["group"] == "audio"
    assert result["sizeBytes"] == 3
    assert "wav" in result["targetFormats"]


def test_targets_can_use_path(tmp_path):
    src = tmp_path / "movie.mp4"
    src.touch()

    result = api.get_targets({"path": str(src)})

    assert result["group"] == "video"
    assert "mp3" in result["targetFormats"]


def test_validate_rejects_incompatible_target(tmp_path):
    src = tmp_path / "photo.png"
    src.touch()

    result = api.validate_job({"inputPath": str(src), "targetFormat": "mp3"})

    assert result["valid"] is False
    assert "não é compatível" in result["errors"][0]


def test_estimate_job_uses_estimator(mocker, tmp_path):
    src = tmp_path / "song.wav"
    src.touch()
    mocker.patch("converter_file.api.estimate_output_size", return_value=1234)

    result = api.estimate_job({"inputPath": str(src), "targetFormat": "mp3"})

    assert result == {
        "inputPath": str(src),
        "targetFormat": "mp3",
        "estimatedSizeBytes": 1234,
    }


def test_convert_job_for_image(mocker, tmp_path):
    src = tmp_path / "photo.png"
    src.touch()
    out = tmp_path / "photo.jpg"
    mock_convert = mocker.patch("converter_file.api.convert_image", return_value=str(out))

    result = api.convert_job({
        "inputPath": str(src),
        "targetFormat": "jpg",
        "outputPath": str(out),
    })

    mock_convert.assert_called_once_with(str(src), "jpg", str(out))
    assert result["ok"] is True
    assert result["outputPath"] == str(out)


def test_convert_job_maps_audio_options(mocker, tmp_path):
    src = tmp_path / "song.wav"
    src.touch()
    out = tmp_path / "song.mp3"
    mock_convert = mocker.patch("converter_file.api.convert_media", return_value=str(out))

    api.convert_job({
        "inputPath": str(src),
        "targetFormat": "mp3",
        "outputPath": str(out),
        "options": {
            "audio": {
                "compressionPreset": "balanced",
                "channels": "mono",
                "normalizeVolume": True,
                "stripMetadata": True,
            }
        },
    })

    options = mock_convert.call_args.kwargs["audio_options"]
    assert options.compression_preset == "balanced"
    assert options.channels == "mono"
    assert options.normalize_volume is True
    assert options.strip_metadata is True


def test_dispatch_rejects_unknown_command():
    with pytest.raises(ValueError, match="Comando inválido"):
        api.dispatch("unknown", {})


def test_main_outputs_json_error(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["converter-file-api", "inspect"])
    monkeypatch.setattr("sys.stdin", _FakeStdin(json.dumps({"path": "/missing/file.mp3"})))

    with pytest.raises(SystemExit) as exc_info:
        api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False


class _FakeStdin:
    def __init__(self, value: str):
        self.value = value

    def read(self) -> str:
        return self.value
