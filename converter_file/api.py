import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from converter_file.audio_options import AudioAdvancedOptions
from converter_file.convert_document import convert_document
from converter_file.convert_image import convert_image
from converter_file.convert_media import convert_media
from converter_file.detect import TARGET_FORMATS, detect_group
from converter_file.document_options import DocumentAdvancedOptions, PdfAdvancedOptions
from converter_file.estimate import estimate_output_size
from converter_file.video_options import VideoAdvancedOptions


def inspect_file(path: str) -> dict[str, Any]:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    group = detect_group(path)
    return {
        "path": str(src),
        "name": src.name,
        "stem": src.stem,
        "extension": src.suffix.lstrip(".").lower(),
        "group": group,
        "sizeBytes": src.stat().st_size,
        "targetFormats": TARGET_FORMATS[group],
    }


def get_targets(payload: dict[str, Any]) -> dict[str, Any]:
    group = payload.get("group")
    path = payload.get("path")
    if group is None and path is not None:
        group = detect_group(path)
    if group not in TARGET_FORMATS:
        raise ValueError(f"Grupo inválido: {group}")
    return {"group": group, "targetFormats": TARGET_FORMATS[group]}


def estimate_job(payload: dict[str, Any]) -> dict[str, Any]:
    input_path = _required_str(payload, "inputPath")
    target_format = _required_str(payload, "targetFormat")
    source_group = payload.get("sourceGroup") or detect_group(input_path)

    size = estimate_output_size([input_path], target_format, source_group)
    return {
        "inputPath": input_path,
        "targetFormat": target_format,
        "estimatedSizeBytes": size,
    }


def validate_job(payload: dict[str, Any]) -> dict[str, Any]:
    input_path = _required_str(payload, "inputPath")
    target_format = _required_str(payload, "targetFormat")
    group = detect_group(input_path)
    errors: list[str] = []
    warnings: list[str] = []

    if target_format not in TARGET_FORMATS[group]:
        errors.append(f"Formato de saída .{target_format} não é compatível com {group}.")

    if group == "pdf" and target_format == "webp":
        warnings.append("PDF para WEBP usa PNG como fallback intermediário.")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "sourceGroup": group,
        "targetFormat": target_format,
    }


def convert_job(
    payload: dict[str, Any],
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict[str, Any]:
    input_path = _required_str(payload, "inputPath")
    target_format = _required_str(payload, "targetFormat")
    output_path = payload.get("outputPath")
    group = detect_group(input_path)

    _emit_progress(progress_callback, 5, "Validando conversão...")
    validation = validate_job(payload)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))

    _emit_progress(progress_callback, 10, "Preparando conversão...")
    if output_path and payload.get("overwriteExistingFiles") and Path(output_path).exists():
        Path(output_path).unlink()
    options = payload.get("options") or {}

    if group == "image":
        _emit_progress(progress_callback, 35, "Convertendo imagem...")
        output = convert_image(input_path, target_format, output_path)
    elif group in {"audio", "video"}:
        output = convert_media(
            input_path,
            target_format,
            output_path,
            audio_options=_audio_options_from_payload(options.get("audio")),
            video_options=_video_options_from_payload(options.get("video")),
            progress_callback=progress_callback,
        )
    elif group == "pdf":
        _emit_progress(progress_callback, 35, "Convertendo documento...")
        output = convert_document(
            input_path,
            target_format,
            output_path,
            pdf_options=_pdf_options_from_payload(options.get("pdf")),
        )
    elif group == "document":
        _emit_progress(progress_callback, 35, "Convertendo documento...")
        output = convert_document(
            input_path,
            target_format,
            output_path,
            document_options=_document_options_from_payload(options.get("document")),
        )
    else:
        raise ValueError(f"Grupo não suportado: {group}")

    _emit_progress(progress_callback, 100, "Conversão concluída.")
    return {
        "ok": True,
        "inputPath": input_path,
        "outputPath": output,
        "sourceGroup": group,
        "targetFormat": target_format,
        "sizeBytes": Path(output).stat().st_size if Path(output).exists() else None,
    }


def dispatch(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    if command == "inspect":
        return inspect_file(_required_str(payload, "path"))
    if command == "targets":
        return get_targets(payload)
    if command == "estimate":
        return estimate_job(payload)
    if command == "validate":
        return validate_job(payload)
    if command == "convert":
        return convert_job(payload)
    raise ValueError(f"Comando inválido: {command}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="converter-file-api",
        description="API JSON não interativa para integrações como Electron.",
    )
    parser.add_argument("command", choices=["inspect", "targets", "estimate", "validate", "convert"])
    parser.add_argument("json_file", nargs="?", help="Arquivo JSON de entrada. Se omitido, lê stdin.")
    parser.add_argument("--progress", action="store_true", help="Emite eventos de progresso em stderr.")
    args = parser.parse_args()

    try:
        payload = _read_payload(args.json_file)
        if args.command == "convert" and args.progress:
            result = convert_job(payload, progress_callback=_write_progress_event)
        else:
            result = dispatch(args.command, payload)
        _write_json({"ok": True, "result": result})
    except Exception as e:
        _write_json({"ok": False, "error": str(e)})
        sys.exit(1)


def _read_payload(json_file: str | None) -> dict[str, Any]:
    if json_file is None:
        raw = sys.stdin.read()
    else:
        raw = Path(json_file).read_text()
    if not raw.strip():
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Payload JSON deve ser um objeto.")
    return data


def _write_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _write_progress_event(percent: int, message: str) -> None:
    payload = {"percent": max(0, min(100, percent)), "message": message}
    print(f"__PROGRESS__{json.dumps(payload, ensure_ascii=False)}", file=sys.stderr, flush=True)


def _emit_progress(
    progress_callback: Callable[[int, str], None] | None,
    percent: int,
    message: str,
) -> None:
    if progress_callback is not None:
        progress_callback(percent, message)


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Campo obrigatório ausente: {key}")
    return value


def _audio_options_from_payload(payload: dict[str, Any] | None) -> AudioAdvancedOptions | None:
    if payload is None:
        return None
    return AudioAdvancedOptions(
        compression_preset=payload.get("compressionPreset", "none"),
        channels=payload.get("channels", "keep"),
        normalize_volume=bool(payload.get("normalizeVolume", False)),
        strip_metadata=bool(payload.get("stripMetadata", False)),
    )


def _video_options_from_payload(payload: dict[str, Any] | None) -> VideoAdvancedOptions | None:
    if payload is None:
        return None
    return VideoAdvancedOptions(
        resolution=payload.get("resolution", "keep"),
        compression_preset=payload.get("compressionPreset", "none"),
        fps=payload.get("fps", "keep"),
        remove_audio=bool(payload.get("removeAudio", False)),
        optimize_for_web=bool(payload.get("optimizeForWeb", False)),
        strip_metadata=bool(payload.get("stripMetadata", False)),
    )


def _pdf_options_from_payload(payload: dict[str, Any] | None) -> PdfAdvancedOptions | None:
    if payload is None:
        return None
    return PdfAdvancedOptions(
        compression_preset=payload.get("compressionPreset", "none"),
        ocr=bool(payload.get("ocr", False)),
        ocr_language=payload.get("ocrLanguage", "auto"),
        searchable_pdf=bool(payload.get("searchablePdf", False)),
        dpi=int(payload.get("dpi", 150)),
        password=payload.get("password"),
        strip_metadata=bool(payload.get("stripMetadata", False)),
    )


def _document_options_from_payload(payload: dict[str, Any] | None) -> DocumentAdvancedOptions | None:
    if payload is None:
        return None
    return DocumentAdvancedOptions(
        pdf_quality=payload.get("pdfQuality", "balanced"),
        preserve_layout=bool(payload.get("preserveLayout", True)),
        extract_text_only=bool(payload.get("extractTextOnly", False)),
        include_images=bool(payload.get("includeImages", True)),
        output_mode=payload.get("outputMode", "single_file"),
        encoding=payload.get("encoding", "utf-8"),
        markdown_flavor=payload.get("markdownFlavor", "github"),
        generate_toc=bool(payload.get("generateToc", False)),
        strip_metadata=bool(payload.get("stripMetadata", False)),
    )


if __name__ == "__main__":
    main()
