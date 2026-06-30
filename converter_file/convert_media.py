import subprocess
from pathlib import Path

from converter_file.audio_options import AudioAdvancedOptions, build_audio_ffmpeg_args
from converter_file.detect import SUPPORTED_FORMATS
from converter_file.video_options import VideoAdvancedOptions, build_video_ffmpeg_args


def convert_media(
    input_path: str,
    target_format: str,
    output_path: str | None = None,
    audio_options: AudioAdvancedOptions | None = None,
    video_options: VideoAdvancedOptions | None = None,
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
            print(f"Aviso: {warning}")
        command.extend(audio_args)
    elif target_format in SUPPORTED_FORMATS["video"]:
        video_args, warnings = build_video_ffmpeg_args(video_options, target_format)
        for warning in warnings:
            print(f"Aviso: {warning}")
        command.extend(video_args)
    command.append(str(dst))

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return str(dst)
