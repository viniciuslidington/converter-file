import pytest

from converter_file.document_options import (
    DEFAULT_DOCUMENT_ADVANCED_OPTIONS,
    DEFAULT_PDF_ADVANCED_OPTIONS,
    DocumentAdvancedOptions,
    PdfAdvancedOptions,
    confirm_editable_document_conversion,
    confirm_pdf_conversion,
    prompt_editable_document_advanced_options,
    prompt_pdf_advanced_options,
)
from converter_file.menu import ConversionCancelled


def test_default_pdf_options_preserve_current_behavior():
    assert DEFAULT_PDF_ADVANCED_OPTIONS == PdfAdvancedOptions(
        compression_preset="none",
        ocr=False,
        ocr_language="auto",
        searchable_pdf=False,
        dpi=150,
        password=None,
        strip_metadata=False,
    )


def test_default_document_options_preserve_current_behavior():
    assert DEFAULT_DOCUMENT_ADVANCED_OPTIONS == DocumentAdvancedOptions(
        pdf_quality="balanced",
        preserve_layout=True,
        extract_text_only=False,
        include_images=True,
        output_mode="single_file",
        encoding="utf-8",
        markdown_flavor="github",
        generate_toc=False,
        strip_metadata=False,
    )


def test_prompt_pdf_options_returns_defaults_when_user_declines(mocker):
    mocker.patch("converter_file.document_options.prompt_yes_no", return_value=False)

    assert prompt_pdf_advanced_options("pdf") == DEFAULT_PDF_ADVANCED_OPTIONS


def test_prompt_pdf_options_collects_ocr_for_txt(mocker):
    mocker.patch("converter_file.document_options.prompt_yes_no", side_effect=[True, True, True])
    mocker.patch("converter_file.document_options.prompt_choice", return_value="por")

    assert prompt_pdf_advanced_options("txt") == PdfAdvancedOptions(
        compression_preset="none",
        ocr=True,
        ocr_language="por",
        searchable_pdf=False,
        dpi=150,
        password=None,
        strip_metadata=True,
    )


def test_prompt_pdf_options_collects_pdf_specific_values(mocker):
    mocker.patch(
        "converter_file.document_options.prompt_yes_no",
        side_effect=[True, True, True, True, True, True],
    )
    mocker.patch("converter_file.document_options.prompt_choice", side_effect=["balanced", "eng"])
    mocker.patch("converter_file.document_options.prompt_text", return_value="secret")

    assert prompt_pdf_advanced_options("pdf") == PdfAdvancedOptions(
        compression_preset="balanced",
        ocr=True,
        ocr_language="eng",
        searchable_pdf=True,
        dpi=150,
        password="secret",
        strip_metadata=True,
    )


def test_prompt_pdf_options_collects_dpi_for_image(mocker):
    mocker.patch("converter_file.document_options.prompt_yes_no", side_effect=[True, False])
    mocker.patch("converter_file.document_options.prompt_choice", return_value=300)

    assert prompt_pdf_advanced_options("png") == PdfAdvancedOptions(dpi=300)


def test_prompt_document_options_returns_defaults_when_user_declines(mocker):
    mocker.patch("converter_file.document_options.prompt_yes_no", return_value=False)

    assert prompt_editable_document_advanced_options("pdf") == DEFAULT_DOCUMENT_ADVANCED_OPTIONS


def test_prompt_document_options_collects_pdf_values(mocker):
    mocker.patch("converter_file.document_options.prompt_choice", return_value="print")
    mocker.patch("converter_file.document_options.prompt_yes_no", side_effect=[True, True, True, True])

    assert prompt_editable_document_advanced_options("pdf") == DocumentAdvancedOptions(
        pdf_quality="print",
        preserve_layout=True,
        generate_toc=True,
        strip_metadata=True,
    )


def test_prompt_document_options_collects_markdown_values(mocker):
    mocker.patch(
        "converter_file.document_options.prompt_yes_no",
        side_effect=[True, True, False, True, True],
    )
    mocker.patch(
        "converter_file.document_options.prompt_choice",
        side_effect=["folder", "latin1", "commonmark"],
    )

    assert prompt_editable_document_advanced_options("md") == DocumentAdvancedOptions(
        extract_text_only=True,
        include_images=False,
        output_mode="folder",
        encoding="latin1",
        markdown_flavor="commonmark",
        generate_toc=True,
        strip_metadata=True,
    )


def test_confirm_pdf_conversion_can_cancel(mocker):
    mocker.patch("converter_file.document_options.prompt_yes_no", return_value=False)

    with pytest.raises(ConversionCancelled):
        confirm_pdf_conversion(["contract.pdf"], "txt", DEFAULT_PDF_ADVANCED_OPTIONS)


def test_confirm_document_conversion_can_cancel(mocker):
    mocker.patch("converter_file.document_options.prompt_yes_no", return_value=False)

    with pytest.raises(ConversionCancelled):
        confirm_editable_document_conversion(["report.docx"], "pdf", DEFAULT_DOCUMENT_ADVANCED_OPTIONS)
