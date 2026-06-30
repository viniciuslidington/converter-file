from dataclasses import dataclass

from converter_file.menu import ConversionCancelled, prompt_choice, prompt_text, prompt_yes_no


@dataclass(frozen=True)
class PdfAdvancedOptions:
    compression_preset: str = "none"
    ocr: bool = False
    ocr_language: str = "auto"
    searchable_pdf: bool = False
    dpi: int = 150
    password: str | None = None
    strip_metadata: bool = False


@dataclass(frozen=True)
class DocumentAdvancedOptions:
    pdf_quality: str = "balanced"
    preserve_layout: bool = True
    extract_text_only: bool = False
    include_images: bool = True
    output_mode: str = "single_file"
    encoding: str = "utf-8"
    markdown_flavor: str = "github"
    generate_toc: bool = False
    strip_metadata: bool = False


DEFAULT_PDF_ADVANCED_OPTIONS = PdfAdvancedOptions()
DEFAULT_DOCUMENT_ADVANCED_OPTIONS = DocumentAdvancedOptions()

PDF_COMPRESSION_CHOICES: list[tuple[str, str]] = [
    ("Nenhuma", "none"),
    ("Arquivo menor", "small"),
    ("Equilibrado", "balanced"),
    ("Alta qualidade", "high_quality"),
]

OCR_LANGUAGE_CHOICES: list[tuple[str, str]] = [
    ("Português", "por"),
    ("Inglês", "eng"),
    ("Espanhol", "spa"),
    ("Detectar automaticamente", "auto"),
]

DPI_CHOICES: list[tuple[str, int]] = [
    ("72 DPI", 72),
    ("150 DPI", 150),
    ("300 DPI", 300),
]

PDF_QUALITY_CHOICES: list[tuple[str, str]] = [
    ("Pequeno", "small"),
    ("Equilibrado", "balanced"),
    ("Impressão", "print"),
]

OUTPUT_MODE_CHOICES: list[tuple[str, str]] = [
    ("Arquivo único", "single_file"),
    ("Pasta com arquivos auxiliares", "folder"),
]

ENCODING_CHOICES: list[tuple[str, str]] = [
    ("UTF-8", "utf-8"),
    ("Latin1", "latin1"),
]

MARKDOWN_FLAVOR_CHOICES: list[tuple[str, str]] = [
    ("GitHub Flavored Markdown", "github"),
    ("CommonMark", "commonmark"),
]

PDF_OCR_TARGETS = {"pdf", "txt", "md", "docx"}
PDF_IMAGE_TARGETS = {"png", "jpg", "webp"}
PRESERVE_LAYOUT_TARGETS = {"pdf", "docx", "odt", "html"}
TEXT_ONLY_TARGETS = {"txt", "md", "html"}
INCLUDE_IMAGES_TARGETS = {"md", "html"}
OUTPUT_MODE_TARGETS = {"html", "md", "png", "jpg", "webp"}
ENCODING_TARGETS = {"txt", "md", "html"}
TOC_TARGETS = {"pdf", "md", "html"}


def prompt_pdf_advanced_options(target_format: str) -> PdfAdvancedOptions:
    wants_advanced = prompt_yes_no("Deseja configurar opções avançadas para o documento?")
    if not wants_advanced:
        return DEFAULT_PDF_ADVANCED_OPTIONS

    compression_preset = "none"
    if target_format == "pdf":
        compression_preset = prompt_choice(
            "Escolha o nível de compressão do PDF:",
            PDF_COMPRESSION_CHOICES,
        )

    ocr = False
    ocr_language = "auto"
    searchable_pdf = False
    if target_format in PDF_OCR_TARGETS:
        ocr = prompt_yes_no("Deseja aplicar OCR?")
        if ocr:
            ocr_language = prompt_choice(
                "Escolha o idioma principal do documento:",
                OCR_LANGUAGE_CHOICES,
            )
            if target_format == "pdf":
                searchable_pdf = prompt_yes_no("Deseja gerar um PDF pesquisável?")

    dpi = 150
    if target_format in PDF_IMAGE_TARGETS:
        dpi = prompt_choice("Escolha a qualidade da imagem:", DPI_CHOICES)

    strip_metadata = prompt_yes_no("Deseja remover metadados do documento?")

    password = None
    if target_format == "pdf" and prompt_yes_no("Deseja proteger o PDF com senha?"):
        password = prompt_text("Digite a senha do PDF:")

    return PdfAdvancedOptions(
        compression_preset=compression_preset,
        ocr=ocr,
        ocr_language=ocr_language,
        searchable_pdf=searchable_pdf,
        dpi=dpi,
        password=password or None,
        strip_metadata=strip_metadata,
    )


def prompt_editable_document_advanced_options(target_format: str) -> DocumentAdvancedOptions:
    wants_advanced = prompt_yes_no("Deseja configurar opções avançadas para o documento?")
    if not wants_advanced:
        return DEFAULT_DOCUMENT_ADVANCED_OPTIONS

    pdf_quality = "balanced"
    if target_format == "pdf":
        pdf_quality = prompt_choice("Escolha a qualidade do PDF:", PDF_QUALITY_CHOICES)

    preserve_layout = True
    if target_format in PRESERVE_LAYOUT_TARGETS:
        preserve_layout = prompt_yes_no("Deseja preservar o layout original?")

    extract_text_only = False
    if target_format in TEXT_ONLY_TARGETS:
        extract_text_only = prompt_yes_no("Deseja extrair apenas o texto puro?")

    include_images = True
    if target_format in INCLUDE_IMAGES_TARGETS:
        include_images = prompt_yes_no("Deseja incluir imagens do documento?")

    output_mode = "single_file"
    if target_format in OUTPUT_MODE_TARGETS:
        output_mode = prompt_choice("Escolha o modo de saída:", OUTPUT_MODE_CHOICES)

    encoding = "utf-8"
    if target_format in ENCODING_TARGETS:
        encoding = prompt_choice("Escolha o encoding:", ENCODING_CHOICES)

    markdown_flavor = "github"
    if target_format == "md":
        markdown_flavor = prompt_choice("Escolha o estilo de Markdown:", MARKDOWN_FLAVOR_CHOICES)

    generate_toc = False
    if target_format in TOC_TARGETS:
        generate_toc = prompt_yes_no("Deseja gerar sumário automaticamente?")

    strip_metadata = prompt_yes_no("Deseja remover metadados do documento?")

    return DocumentAdvancedOptions(
        pdf_quality=pdf_quality,
        preserve_layout=preserve_layout,
        extract_text_only=extract_text_only,
        include_images=include_images,
        output_mode=output_mode,
        encoding=encoding,
        markdown_flavor=markdown_flavor,
        generate_toc=generate_toc,
        strip_metadata=strip_metadata,
    )


def confirm_pdf_conversion(
    input_paths: list[str],
    output_format: str,
    options: PdfAdvancedOptions,
) -> None:
    print("\nResumo da conversão:")
    _print_inputs(input_paths)
    print(f"* Formato de saída: {output_format}")
    print(f"* Compressão: {options.compression_preset}")
    print(f"* OCR: {options.ocr}")
    print(f"* Idioma OCR: {options.ocr_language}")
    print(f"* PDF pesquisável: {options.searchable_pdf}")
    print(f"* DPI: {options.dpi}")
    print(f"* Proteger com senha: {options.password is not None}")
    print(f"* Remover metadados: {options.strip_metadata}")
    if not prompt_yes_no("Confirmar conversão?"):
        raise ConversionCancelled


def confirm_editable_document_conversion(
    input_paths: list[str],
    output_format: str,
    options: DocumentAdvancedOptions,
) -> None:
    print("\nResumo da conversão:")
    _print_inputs(input_paths)
    print(f"* Formato de saída: {output_format}")
    print(f"* Qualidade PDF: {options.pdf_quality}")
    print(f"* Preservar layout: {options.preserve_layout}")
    print(f"* Extrair apenas texto: {options.extract_text_only}")
    print(f"* Incluir imagens: {options.include_images}")
    print(f"* Modo de saída: {options.output_mode}")
    print(f"* Encoding: {options.encoding}")
    print(f"* Markdown flavor: {options.markdown_flavor}")
    print(f"* Gerar sumário: {options.generate_toc}")
    print(f"* Remover metadados: {options.strip_metadata}")
    if not prompt_yes_no("Confirmar conversão?"):
        raise ConversionCancelled


def _print_inputs(input_paths: list[str]) -> None:
    if len(input_paths) == 1:
        print(f"* Entrada: {input_paths[0]}")
    else:
        print(f"* Entradas: {len(input_paths)} arquivos")
