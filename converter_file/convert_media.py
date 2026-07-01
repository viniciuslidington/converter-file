import subprocess
import sys
from pathlib import Path
from typing import Callable

from converter_file.audio_options import AudioAdvancedOptions, build_audio_ffmpeg_args
from converter_file.detect import SUPPORTED_FORMATS
from converter_file.video_options import VideoAdvancedOptions, build_video_ffmpeg_args


def convert_media(
    input_path: str,
    target_format: str,
    output_path: str | None = None,
    audio_options: AudioAdvancedOptions | None = None,
    video_options: VideoAdvancedOptions | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    dst = Path(output_path) if output_path else src.with_suffix(f".{target_format}")
    if dst.exists():
        raise FileExistsError(f"Arquivo de saída já existe: {dst}")

    command = ["ffmpeg", "-i", str(src)]
    if target_format in SUPPORTED_FORMATS["audio"]:
        command.append("-vn")
        audio_args, warnings = build_audio_ffmpeg_args(audio_options, target_format)
        for warning in warnings:
            print(f"Aviso: {warning}", file=sys.stderr)
        command.extend(audio_args)
    elif target_format in SUPPORTED_FORMATS["video"]:
        video_args, warnings = build_video_ffmpeg_args(video_options, target_format)
        for warning in warnings:
            print(f"Aviso: {warning}", file=sys.stderr)
        command.extend(video_args)
    command.append(str(dst))

    if progress_callback is not None:
        _run_ffmpeg_with_progress(command, src, progress_callback)
        return str(dst)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return str(dst)


def _run_ffmpeg_with_progress(
    command: list[str],
    src: Path,
    progress_callback: Callable[[int, str], None],
) -> None:
    duration_seconds = _probe_duration_seconds(src)
    progress_command = [
        command[0],
        "-nostats",
        "-progress",
        "pipe:1",
        *command[1:],
    ]
    process = subprocess.Popen(
        progress_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output_chunks: list[str] = []

    assert process.stdout is not None
    for line in process.stdout:
        key, _, value = line.strip().partition("=")
        if key == "out_time_ms" and duration_seconds > 0:
            elapsed_seconds = int(value or "0") / 1_000_000
            percent = min(95, max(12, int((elapsed_seconds / duration_seconds) * 90)))
            progress_callback(percent, "Convertendo mídia...")
        elif key == "progress" and value == "end":
            progress_callback(95, "Finalizando arquivo...")
        elif not key or key not in {
            "bitrate",
            "drop_frames",
            "dup_frames",
            "fps",
            "out_time",
            "out_time_ms",
            "out_time_us",
            "progress",
            "speed",
            "stream_0_0_q",
            "total_size",
        }:
            output_chunks.append(line)

    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError("".join(output_chunks))


def _probe_duration_seconds(src: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(src),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0
