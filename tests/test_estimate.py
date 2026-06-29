from unittest.mock import MagicMock

from converter_file.estimate import (
    estimate_output_size,
    estimate_output_size_labels,
    format_file_size,
)


def test_format_file_size():
    assert format_file_size(512) == "512 B"
    assert format_file_size(1536) == "1.5 KB"
    assert format_file_size(2 * 1024 * 1024) == "2.0 MB"


def test_estimates_audio_target_from_duration(mocker):
    mocker.patch(
        "converter_file.estimate._probe_media",
        return_value={"duration": 10.0, "bit_rate": 1_000_000, "size": None},
    )

    assert estimate_output_size(["clip.mp4"], "mp3", "video") == 240_000


def test_estimates_video_target_from_source_bitrate(mocker):
    mocker.patch(
        "converter_file.estimate._probe_media",
        return_value={"duration": 10.0, "bit_rate": 800_000, "size": None},
    )

    assert estimate_output_size(["clip.mov"], "mp4", "video") == 1_000_000


def test_estimate_labels_sum_batch(mocker):
    mocker.patch(
        "converter_file.estimate.estimate_single_output_size",
        side_effect=[1024, 2048],
    )

    labels = estimate_output_size_labels(["a.wav", "b.wav"], ["mp3"], "audio")

    assert labels == {"mp3": "~3.0 KB"}


def test_estimate_returns_none_when_any_file_is_unknown(mocker):
    mocker.patch(
        "converter_file.estimate.estimate_single_output_size",
        side_effect=[1024, None],
    )

    assert estimate_output_size(["a.wav", "b.wav"], "mp3", "audio") is None


def test_probe_media_parses_ffprobe_json(mocker):
    from converter_file.estimate import _probe_media

    mocker.patch(
        "subprocess.run",
        return_value=MagicMock(
            returncode=0,
            stdout='{"format": {"duration": "12.5", "bit_rate": "192000", "size": "300000"}}',
        ),
    )

    assert _probe_media("song.mp3") == {
        "duration": 12.5,
        "bit_rate": 192_000,
        "size": 300_000,
    }
