import pytest

from converter_file.audio_options import (
    AudioAdvancedOptions,
    DEFAULT_AUDIO_ADVANCED_OPTIONS,
    build_audio_ffmpeg_args,
    confirm_audio_conversion,
    prompt_audio_advanced_options,
)
from converter_file.menu import ConversionCancelled


def test_default_audio_options_preserve_current_behavior():
    assert DEFAULT_AUDIO_ADVANCED_OPTIONS == AudioAdvancedOptions(
        compression_preset="none",
        channels="keep",
        normalize_volume=False,
        strip_metadata=False,
    )
    assert build_audio_ffmpeg_args(DEFAULT_AUDIO_ADVANCED_OPTIONS, "mp3") == ([], [])


def test_build_audio_ffmpeg_args_for_advanced_options():
    options = AudioAdvancedOptions(
        compression_preset="balanced",
        channels="mono",
        normalize_volume=True,
        strip_metadata=True,
    )

    args, warnings = build_audio_ffmpeg_args(options, "mp3")

    assert warnings == []
    assert args == ["-b:a", "192k", "-ac", "1", "-af", "loudnorm", "-map_metadata", "-1"]


def test_build_audio_ffmpeg_args_for_stereo_high_quality():
    options = AudioAdvancedOptions(compression_preset="high_quality", channels="stereo")

    args, warnings = build_audio_ffmpeg_args(options, "ogg")

    assert warnings == []
    assert args == ["-b:a", "320k", "-ac", "2"]


def test_ignores_bitrate_compression_for_wav_with_warning():
    options = AudioAdvancedOptions(compression_preset="small")

    args, warnings = build_audio_ffmpeg_args(options, "wav")

    assert args == []
    assert "Compressão por bitrate ignorada" in warnings[0]


def test_prompt_audio_options_returns_defaults_when_user_declines(mocker):
    mocker.patch("converter_file.audio_options.prompt_yes_no", return_value=False)

    assert prompt_audio_advanced_options() == DEFAULT_AUDIO_ADVANCED_OPTIONS


def test_prompt_audio_options_collects_values(mocker):
    mocker.patch("converter_file.audio_options.prompt_yes_no", side_effect=[True, True, False])
    mocker.patch("converter_file.audio_options.prompt_choice", side_effect=["balanced", "mono"])

    assert prompt_audio_advanced_options() == AudioAdvancedOptions(
        compression_preset="balanced",
        channels="mono",
        normalize_volume=True,
        strip_metadata=False,
    )


def test_confirm_audio_conversion_can_cancel(mocker):
    mocker.patch("converter_file.audio_options.prompt_yes_no", return_value=False)

    with pytest.raises(ConversionCancelled):
        confirm_audio_conversion(["song.mp3"], "ogg", DEFAULT_AUDIO_ADVANCED_OPTIONS)
