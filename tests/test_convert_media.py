import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
from converter_file.audio_options import AudioAdvancedOptions
from converter_file.convert_media import convert_media
from converter_file.video_options import VideoAdvancedOptions


def test_raises_if_input_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert_media(str(tmp_path / "nope.mp4"), "avi")


def test_raises_if_output_exists(tmp_path):
    src = tmp_path / "video.mp4"
    src.touch()
    dst = tmp_path / "video.avi"
    dst.touch()
    with pytest.raises(FileExistsError, match="já existe"):
        convert_media(str(src), "avi")


def test_calls_ffmpeg_with_correct_args(tmp_path, mocker):
    src = tmp_path / "video.mp4"
    src.touch()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0, stderr="")

    result = convert_media(str(src), "avi")

    assert result == str(tmp_path / "video.avi")
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "ffmpeg"
    assert str(src) in call_args
    assert str(tmp_path / "video.avi") in call_args


def test_extracts_audio_without_video_stream(tmp_path, mocker):
    src = tmp_path / "video.mp4"
    src.touch()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0, stderr="")

    result = convert_media(str(src), "mp3")

    assert result == str(tmp_path / "video.mp3")
    assert mock_run.call_args[0][0] == [
        "ffmpeg",
        "-i",
        str(src),
        "-vn",
        str(tmp_path / "video.mp3"),
    ]


def test_applies_audio_advanced_options(tmp_path, mocker):
    src = tmp_path / "song.wav"
    src.touch()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0, stderr="")

    options = AudioAdvancedOptions(
        compression_preset="balanced",
        channels="mono",
        normalize_volume=True,
        strip_metadata=True,
    )

    result = convert_media(str(src), "mp3", audio_options=options)

    assert result == str(tmp_path / "song.mp3")
    assert mock_run.call_args[0][0] == [
        "ffmpeg",
        "-i",
        str(src),
        "-vn",
        "-b:a",
        "192k",
        "-ac",
        "1",
        "-af",
        "loudnorm",
        "-map_metadata",
        "-1",
        str(tmp_path / "song.mp3"),
    ]


def test_applies_video_advanced_options(tmp_path, mocker):
    src = tmp_path / "video.mov"
    src.touch()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0, stderr="")

    options = VideoAdvancedOptions(
        resolution="720p",
        compression_preset="balanced",
        fps=30,
        remove_audio=True,
        optimize_for_web=True,
        strip_metadata=True,
    )

    result = convert_media(str(src), "mp4", video_options=options)

    assert result == str(tmp_path / "video.mp4")
    assert mock_run.call_args[0][0] == [
        "ffmpeg",
        "-i",
        str(src),
        "-vf",
        "scale=-2:min(720\\,ih)",
        "-crf",
        "26",
        "-r",
        "30",
        "-an",
        "-movflags",
        "+faststart",
        "-map_metadata",
        "-1",
        str(tmp_path / "video.mp4"),
    ]


def test_raises_on_ffmpeg_failure(tmp_path, mocker):
    src = tmp_path / "video.mp4"
    src.touch()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=1, stderr="ffmpeg error details")

    with pytest.raises(RuntimeError, match="ffmpeg error details"):
        convert_media(str(src), "avi")
