import shutil
import subprocess
import sys
from pathlib import Path

from converter_file.detect import detect_group
from converter_file.document_options import (
    DEFAULT_DOCUMENT_ADVANCED_OPTIONS,
    DEFAULT_PDF_ADVANCED_OPTIONS,
    DocumentAdvancedOptions,
    PdfAdvancedOptions,
)

PDF_COMPRESSION_ARGS = {
    "small": ["--stream-data=compress", "--object-streams=generate", "--recompress-flate"],
    "balanced": ["--stream-data=compress", "--object-streams=generate"],
    "high_quality": ["--stream-data=preserve"],
}

PANDOC_PDF_ENGINE = "weasyprint"

MARKDOWN_WRITERS = {
    "github": "gfm",
    "commonmark": "commonmark",
}


def convert_document(
    input_path: str,
    target_format: str,
    output_path: str | None = None,
    pdf_options: PdfAdvancedOptions | None = None,
    document_options: DocumentAdvancedOptions | None = None,
) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    dst = Path(output_path) if output_path else src.with_suffix(f".{target_format}")
    if dst.exists():
        raise FileExistsError(f"Arquivo de saída já existe: {dst}")

    group = detect_group(str(src))
    if group == "pdf":
        commands, warnings = build_pdf_commands(src, dst, target_format, pdf_options)
    elif group == "document":
        commands, warnings = build_editable_document_commands(src, dst, target_format, document_options)
    else:
        raise ValueError(f"Grupo não suportado para documentos: {group}")

    for warning in warnings:
        print(f"Aviso: {warning}", file=sys.stderr)

    if not commands:
        shutil.copyfile(src, dst)
        return str(dst)

    for command in commands:
        result = _run_external_command(command)
        if result.returncode != 0:
            raise RuntimeError(_format_command_error(result.stderr))

    return str(dst)


def _run_external_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError as e:
        executable = command[0]
        raise RuntimeError(_missing_dependency_message(executable)) from e


def _missing_dependency_message(executable: str) -> str:
    hints = {
        "pandoc": (
            "Pandoc não está instalado ou não está no PATH. "
            "Instale com: macOS `brew install pandoc`; Linux `sudo apt install pandoc`; "
            "Windows `winget install --id JohnMacFarlane.Pandoc`."
        ),
        "pdftotext": (
            "Poppler não está instalado ou não está no PATH. "
            "Instale com: macOS `brew install poppler`; Linux `sudo apt install poppler-utils`."
        ),
        "pdftoppm": (
            "Poppler não está instalado ou não está no PATH. "
            "Instale com: macOS `brew install poppler`; Linux `sudo apt install poppler-utils`."
        ),
        "pdftohtml": (
            "Poppler não está instalado ou não está no PATH. "
            "Instale com: macOS `brew install poppler`; Linux `sudo apt install poppler-utils`."
        ),
        "qpdf": (
            "qpdf não está instalado ou não está no PATH. "
            "Instale com: macOS `brew install qpdf`; Linux `sudo apt install qpdf`."
        ),
        "ocrmypdf": (
            "OCRmyPDF não está instalado ou não está no PATH. "
            "Instale com: macOS `brew install ocrmypdf`; Linux `sudo apt install ocrmypdf`."
        ),
        "weasyprint": (
            "WeasyPrint não está instalado ou não está no PATH. "
            "Rode `./install.sh` ou instale o pacote Python com `python3.11 -m pip install -e .`."
        ),
    }
    return hints.get(
        executable,
        f"Dependência externa não encontrada: {executable}. Instale a ferramenta e tente novamente.",
    )


def _format_command_error(stderr: str) -> str:
    lowered = stderr.lower()
    if "pdflatex" in lowered and "not found" in lowered:
        return (
            "Pandoc tentou usar pdflatex, mas LaTeX não está instalado. "
            "Atualize as dependências com `./install.sh` para usar WeasyPrint como motor de PDF."
        )
    if "weasyprint" in lowered and "not found" in lowered:
        return _missing_dependency_message("weasyprint")
    return stderr


def build_pdf_commands(
    src: Path,
    dst: Path,
    target_format: str,
    options: PdfAdvancedOptions | None,
) -> tuple[list[list[str]], list[str]]:
    advanced_enabled = options is not None
    if options is None:
        options = DEFAULT_PDF_ADVANCED_OPTIONS

    warnings: list[str] = []
    target_format = target_format.lower()

    if target_format == "pdf":
        if not advanced_enabled:
            return [], warnings
        return _build_pdf_to_pdf_commands(src, dst, options)

    if target_format in {"png", "jpg"}:
        image_format = "jpeg" if target_format == "jpg" else "png"
        prefix = str(dst.with_suffix(""))
        return [
            ["pdftoppm", "-singlefile", "-r", str(options.dpi), f"-{image_format}", str(src), prefix]
        ], warnings

    if target_format == "webp":
        warnings.append("Saída WEBP de PDF requer ferramenta externa não padronizada; usando pdftoppm PNG como fallback.")
        prefix = str(dst.with_suffix(""))
        return [["pdftoppm", "-singlefile", "-r", str(options.dpi), "-png", str(src), prefix]], warnings

    if target_format == "txt":
        if advanced_enabled and options.ocr:
            warnings.append("OCR para TXT requer etapa externa com ocrmypdf; usando extração de texto padrão.")
        return [["pdftotext", str(src), str(dst)]], warnings

    if target_format == "html":
        if advanced_enabled and options.ocr:
            warnings.append("OCR para HTML requer etapa externa com ocrmypdf; usando extração HTML padrão.")
        if advanced_enabled and options.strip_metadata:
            warnings.append("Remoção de metadados não se aplica à saída HTML gerada por pdftohtml.")
        return [["pdftohtml", "-s", "-noframes", str(src), str(dst)]], warnings

    if advanced_enabled and options.ocr:
        warnings.append("OCR para este formato requer ocrmypdf; usando conversão padrão.")
    return [["pandoc", str(src), "-o", str(dst)]], warnings


def build_editable_document_commands(
    src: Path,
    dst: Path,
    target_format: str,
    options: DocumentAdvancedOptions | None,
) -> tuple[list[list[str]], list[str]]:
    advanced_enabled = options is not None
    if options is None:
        options = DEFAULT_DOCUMENT_ADVANCED_OPTIONS

    command = ["pandoc", str(src), "-o", str(dst)]
    warnings: list[str] = []

    if target_format == "pdf":
        pdf_engine = shutil.which(PANDOC_PDF_ENGINE) or PANDOC_PDF_ENGINE
        command.append(f"--pdf-engine={pdf_engine}")
        if advanced_enabled and options.pdf_quality != "balanced":
            warnings.append("Qualidade do PDF depende do motor weasyprint; usando configuração padrão.")

    if advanced_enabled and target_format == "md":
        command.extend(["-t", MARKDOWN_WRITERS.get(options.markdown_flavor, "gfm")])

    if advanced_enabled and options.extract_text_only and target_format in {"txt", "md"}:
        command.extend(["-t", "plain" if target_format == "txt" else "plain"])
    elif advanced_enabled and options.extract_text_only and target_format == "html":
        warnings.append("Texto puro em HTML preserva a estrutura mínima do HTML.")

    if advanced_enabled and options.output_mode == "folder" and target_format in {"html", "md", "png", "jpg", "webp"}:
        media_folder = dst.with_suffix("")
        command.extend(["--extract-media", str(media_folder)])

    if advanced_enabled and not options.include_images and target_format in {"md", "html"}:
        warnings.append("Remoção de imagens depende do conversor; exportando conteúdo principal.")

    if advanced_enabled and options.encoding == "latin1" and target_format in {"txt", "md", "html"}:
        command.extend(["--metadata", "charset=latin1"])

    if advanced_enabled and options.generate_toc and target_format in {"pdf", "md", "html"}:
        command.append("--toc")

    if advanced_enabled and not options.preserve_layout and target_format in {"pdf", "docx", "odt", "html"}:
        warnings.append("Preservação de layout desativada; a conversão priorizará a estrutura do conteúdo.")

    if advanced_enabled and options.strip_metadata:
        warnings.append("Remoção de metadados em documentos editáveis depende do backend de conversão.")

    return [command], warnings


def _build_pdf_to_pdf_commands(
    src: Path,
    dst: Path,
    options: PdfAdvancedOptions,
) -> tuple[list[list[str]], list[str]]:
    qpdf_args = PDF_COMPRESSION_ARGS.get(options.compression_preset, [])
    warnings: list[str] = []

    if options.ocr:
        language = "" if options.ocr_language == "auto" else options.ocr_language
        command = ["ocrmypdf"]
        if language:
            command.extend(["-l", language])
        if not options.searchable_pdf:
            command.append("--skip-text")
        command.extend([str(src), str(dst)])
        if options.password:
            warnings.append("Proteção por senha não é aplicada junto com OCR neste fluxo.")
        if qpdf_args:
            warnings.append("Compressão por qpdf não é aplicada junto com OCR neste fluxo.")
        if options.strip_metadata:
            warnings.append("Remoção de metadados não é aplicada junto com OCR neste fluxo.")
        return [command], warnings

    if options.password:
        command = [
            "qpdf",
            *qpdf_args,
            "--encrypt",
            options.password,
            options.password,
            "256",
            "--",
            str(src),
            str(dst),
        ]
        if options.strip_metadata:
            warnings.append("Remoção de metadados em PDF protegido depende do backend qpdf.")
        return [command], warnings

    if qpdf_args or options.strip_metadata:
        command = ["qpdf", *qpdf_args, str(src), str(dst)]
        if options.strip_metadata:
            warnings.append("Remoção de metadados em PDF depende do backend qpdf.")
        return [command], warnings

    return [], warnings
