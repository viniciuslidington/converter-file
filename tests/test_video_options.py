import pytest

from converter_file.menu import ConversionCancelled
from converter_file.video_options import (
    DEFAULT_VIDEO_ADVANCED_OPTIONS,
    VideoAdvancedOptions,
    build_video_ffmpeg_args,
    confirm_video_conversion,
    prompt_video_advanced_options,
)


def test_default_video_options_preserve_current_behavior():
    assert DEFAULT_VIDEO_ADVANCED_OPTIONS == VideoAdvancedOptions(
        resolution="keep",
        compression_preset="none",
        fps="keep",
        remove_audio=False,
        optimize_for_web=False,
        strip_metadata=False,
    )
    assert build_video_ffmpeg_args(DEFAULT_VIDEO_ADVANCED_OPTIONS, "mp4") == ([], [])


def test_build_video_ffmpeg_args_for_advanced_options():
    options = VideoAdvancedOptions(
        resolution="720p",
        compression_preset="balanced",
        fps=30,
        remove_audio=True,
        optimize_for_web=True,
        strip_metadata=True,
    )

    args, warnings = build_video_ffmpeg_args(options, "mp4")

    assert warnings == []
    assert args == [
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
    ]


def test_build_video_ffmpeg_args_for_small_webm():
    options = VideoAdvancedOptions(compression_preset="small")

    args, warnings = build_video_ffmpeg_args(options, "webm")

    assert warnings == []
    assert args == ["-crf", "32"]


def test_ignores_web_optimization_for_non_mp4_with_warning():
    options = VideoAdvancedOptions(optimize_for_web=True)

    args, warnings = build_video_ffmpeg_args(options, "webm")

    assert args == []
    assert "Otimização para web ignorada" in warnings[0]


def test_prompt_video_options_returns_defaults_when_user_declines(mocker):
    mocker.patch("converter_file.video_options.prompt_yes_no", return_value=False)

    assert prompt_video_advanced_options("mp4") == DEFAULT_VIDEO_ADVANCED_OPTIONS


def test_prompt_video_options_collects_values_for_mp4(mocker):
    mocker.patch(
        "converter_file.video_options.prompt_choice",
        side_effect=["720p", "balanced", 30],
    )
    mocker.patch(
        "converter_file.video_options.prompt_yes_no",
        side_effect=[True, True, True, False],
    )

    assert prompt_video_advanced_options("mp4") == VideoAdvancedOptions(
        resolution="720p",
        compression_preset="balanced",
        fps=30,
        remove_audio=True,
        optimize_for_web=True,
        strip_metadata=False,
    )


def test_prompt_video_options_skips_web_optimization_for_non_mp4(mocker):
    mocker.patch(
        "converter_file.video_options.prompt_choice",
        side_effect=["keep", "none", "keep"],
    )
    mocker.patch(
        "converter_file.video_options.prompt_yes_no",
        side_effect=[True, False, True],
    )

    assert prompt_video_advanced_options("webm") == VideoAdvancedOptions(
        resolution="keep",
        compression_preset="none",
        fps="keep",
        remove_audio=False,
        optimize_for_web=False,
        strip_metadata=True,
    )


def test_confirm_video_conversion_can_cancel(mocker):
    mocker.patch("converter_file.video_options.prompt_yes_no", return_value=False)

    with pytest.raises(ConversionCancelled):
        confirm_video_conversion(["movie.mp4"], "mp4", DEFAULT_VIDEO_ADVANCED_OPTIONS)
