from dataclasses import dataclass

from converter_file.menu import ConversionCancelled, prompt_choice, prompt_yes_no


@dataclass(frozen=True)
class VideoAdvancedOptions:
    resolution: str = "keep"
    compression_preset: str = "none"
    fps: str | int = "keep"
    remove_audio: bool = False
    optimize_for_web: bool = False
    strip_metadata: bool = False


DEFAULT_VIDEO_ADVANCED_OPTIONS = VideoAdvancedOptions()

RESOLUTION_CHOICES: list[tuple[str, str]] = [
    ("Manter original", "keep"),
    ("480p", "480p"),
    ("720p", "720p"),
    ("1080p", "1080p"),
    ("4K", "2160p"),
]

COMPRESSION_CHOICES: list[tuple[str, str]] = [
    ("Nenhuma", "none"),
    ("Arquivo menor", "small"),
    ("Equilibrado", "balanced"),
    ("Alta qualidade", "high_quality"),
]

FPS_CHOICES: list[tuple[str, str | int]] = [
    ("Manter original", "keep"),
    ("24 FPS", 24),
    ("30 FPS", 30),
    ("60 FPS", 60),
]

RESOLUTION_HEIGHTS = {
    "480p": 480,
    "720p": 720,
    "1080p": 1080,
    "2160p": 2160,
}

CRF_BY_PRESET = {
    "small": "32",
    "balanced": "26",
    "high_quality": "20",
}


def prompt_video_advanced_options(target_format: str) -> VideoAdvancedOptions:
    wants_advanced = prompt_yes_no("Deseja configurar opções avançadas para o vídeo?")
    if not wants_advanced:
        return DEFAULT_VIDEO_ADVANCED_OPTIONS

    resolution = prompt_choice(
        "Escolha a resolução de saída:",
        RESOLUTION_CHOICES,
    )
    compression_preset = prompt_choice(
        "Escolha o nível de compressão:",
        COMPRESSION_CHOICES,
    )
    fps = prompt_choice(
        "Escolha o FPS de saída:",
        FPS_CHOICES,
    )
    remove_audio = prompt_yes_no("Deseja remover o áudio do vídeo?")
    optimize_for_web = False
    if target_format == "mp4":
        optimize_for_web = prompt_yes_no("Deseja otimizar o vídeo para web?")
    strip_metadata = prompt_yes_no("Deseja remover metadados do vídeo?")

    return VideoAdvancedOptions(
        resolution=resolution,
        compression_preset=compression_preset,
        fps=fps,
        remove_audio=remove_audio,
        optimize_for_web=optimize_for_web,
        strip_metadata=strip_metadata,
    )


def build_video_ffmpeg_args(
    options: VideoAdvancedOptions | None,
    target_format: str,
) -> tuple[list[str], list[str]]:
    if options is None:
        options = DEFAULT_VIDEO_ADVANCED_OPTIONS

    args: list[str] = []
    warnings: list[str] = []

    scale_filter = _scale_filter_for_resolution(options.resolution)
    if scale_filter is not None:
        args.extend(["-vf", scale_filter])

    crf = CRF_BY_PRESET.get(options.compression_preset)
    if crf is not None:
        args.extend(["-crf", crf])

    if options.fps != "keep":
        args.extend(["-r", str(options.fps)])

    if options.remove_audio:
        args.append("-an")

    if options.optimize_for_web:
        if target_format == "mp4":
            args.extend(["-movflags", "+faststart"])
        else:
            warnings.append(
                f"Otimização para web ignorada para .{target_format}; "
                "essa opção é aplicada somente em MP4."
            )

    if options.strip_metadata:
        args.extend(["-map_metadata", "-1"])

    return args, warnings


def print_video_conversion_summary(
    input_paths: list[str],
    output_format: str,
    options: VideoAdvancedOptions,
) -> None:
    print("\nResumo da conversão:")
    if len(input_paths) == 1:
        print(f"* Entrada: {input_paths[0]}")
    else:
        print(f"* Entradas: {len(input_paths)} arquivos")
    print(f"* Formato de saída: {output_format}")
    print(f"* Resolução: {options.resolution}")
    print(f"* Compressão: {options.compression_preset}")
    print(f"* FPS: {options.fps}")
    print(f"* Remover áudio: {options.remove_audio}")
    print(f"* Otimizar para web: {options.optimize_for_web}")
    print(f"* Remover metadados: {options.strip_metadata}")


def confirm_video_conversion(
    input_paths: list[str],
    output_format: str,
    options: VideoAdvancedOptions,
) -> None:
    print_video_conversion_summary(input_paths, output_format, options)
    if not prompt_yes_no("Confirmar conversão?"):
        raise ConversionCancelled


def _scale_filter_for_resolution(resolution: str) -> str | None:
    height = RESOLUTION_HEIGHTS.get(resolution)
    if height is None:
        return None
    return f"scale=-2:min({height}\\,ih)"
