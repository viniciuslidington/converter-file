from dataclasses import dataclass

from converter_file.menu import ConversionCancelled, prompt_choice, prompt_yes_no


@dataclass(frozen=True)
class AudioAdvancedOptions:
    compression_preset: str = "none"
    channels: str = "keep"
    normalize_volume: bool = False
    strip_metadata: bool = False


DEFAULT_AUDIO_ADVANCED_OPTIONS = AudioAdvancedOptions()

COMPRESSION_CHOICES: list[tuple[str, str]] = [
    ("Nenhuma", "none"),
    ("Arquivo menor", "small"),
    ("Equilibrado", "balanced"),
    ("Alta qualidade", "high_quality"),
]

CHANNEL_CHOICES: list[tuple[str, str]] = [
    ("Manter original", "keep"),
    ("Mono", "mono"),
    ("Stereo", "stereo"),
]

LOSSLESS_OR_UNCOMPRESSED_FORMATS = {"wav", "flac"}
BITRATE_BY_PRESET = {
    "small": "96k",
    "balanced": "192k",
    "high_quality": "320k",
}


def prompt_audio_advanced_options() -> AudioAdvancedOptions:
    wants_advanced = prompt_yes_no("Deseja configurar opções avançadas para o áudio?")
    if not wants_advanced:
        return DEFAULT_AUDIO_ADVANCED_OPTIONS

    compression_preset = prompt_choice(
        "Escolha o nível de compressão:",
        COMPRESSION_CHOICES,
    )
    channels = prompt_choice(
        "Deseja alterar os canais do áudio?",
        CHANNEL_CHOICES,
    )
    normalize_volume = prompt_yes_no("Deseja normalizar o volume?")
    strip_metadata = prompt_yes_no("Deseja remover metadados do arquivo?")

    return AudioAdvancedOptions(
        compression_preset=compression_preset,
        channels=channels,
        normalize_volume=normalize_volume,
        strip_metadata=strip_metadata,
    )


def build_audio_ffmpeg_args(
    options: AudioAdvancedOptions | None,
    target_format: str,
) -> tuple[list[str], list[str]]:
    if options is None:
        options = DEFAULT_AUDIO_ADVANCED_OPTIONS

    args: list[str] = []
    warnings: list[str] = []

    bitrate = _bitrate_for_preset(options.compression_preset, target_format)
    if bitrate is not None:
        args.extend(["-b:a", bitrate])
    elif options.compression_preset != "none" and target_format in LOSSLESS_OR_UNCOMPRESSED_FORMATS:
        warnings.append(
            f"Compressão por bitrate ignorada para .{target_format}; "
            "o formato preserva áudio sem perda ou sem compressão por bitrate."
        )

    if options.channels == "mono":
        args.extend(["-ac", "1"])
    elif options.channels == "stereo":
        args.extend(["-ac", "2"])

    if options.normalize_volume:
        args.extend(["-af", "loudnorm"])

    if options.strip_metadata:
        args.extend(["-map_metadata", "-1"])

    return args, warnings


def print_audio_conversion_summary(
    input_paths: list[str],
    output_format: str,
    options: AudioAdvancedOptions,
) -> None:
    print("\nResumo da conversão:")
    if len(input_paths) == 1:
        print(f"* Entrada: {input_paths[0]}")
    else:
        print(f"* Entradas: {len(input_paths)} arquivos")
    print(f"* Formato de saída: {output_format}")
    print(f"* Compressão: {options.compression_preset}")
    print(f"* Canais: {options.channels}")
    print(f"* Normalizar volume: {options.normalize_volume}")
    print(f"* Remover metadados: {options.strip_metadata}")


def confirm_audio_conversion(
    input_paths: list[str],
    output_format: str,
    options: AudioAdvancedOptions,
) -> None:
    print_audio_conversion_summary(input_paths, output_format, options)
    if not prompt_yes_no("Confirmar conversão?"):
        raise ConversionCancelled


def _bitrate_for_preset(compression_preset: str, target_format: str) -> str | None:
    if compression_preset == "none":
        return None
    if target_format in LOSSLESS_OR_UNCOMPRESSED_FORMATS:
        return None
    return BITRATE_BY_PRESET.get(compression_preset)
