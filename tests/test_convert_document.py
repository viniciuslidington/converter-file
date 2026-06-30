from unittest.mock import MagicMock

import pytest

from converter_file.convert_document import (
    build_editable_document_commands,
    build_pdf_commands,
    convert_document,
)
from converter_file.document_options import DocumentAdvancedOptions, PdfAdvancedOptions


def test_convert_document_raises_if_input_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert_document(str(tmp_path / "missing.docx"), "pdf")


def test_convert_document_raises_if_output_exists(tmp_path):
    src = tmp_path / "report.docx"
    dst = tmp_path / "report.pdf"
    src.touch()
    dst.touch()

    with pytest.raises(FileExistsError):
        convert_document(str(src), "pdf")


def test_pdf_to_pdf_without_options_copies_file(tmp_path):
    src = tmp_path / "contract.pdf"
    dst = tmp_path / "out.pdf"
    src.write_bytes(b"pdf")

    assert convert_document(str(src), "pdf", str(dst)) == str(dst)
    assert dst.read_bytes() == b"pdf"


def test_pdf_to_pdf_with_compression_and_password_builds_qpdf_command(tmp_path):
    src = tmp_path / "contract.pdf"
    dst = tmp_path / "out.pdf"
    options = PdfAdvancedOptions(compression_preset="balanced", password="secret")

    commands, warnings = build_pdf_commands(src, dst, "pdf", options)

    assert warnings == []
    assert commands == [[
        "qpdf",
        "--stream-data=compress",
        "--object-streams=generate",
        "--encrypt",
        "secret",
        "secret",
        "256",
        "--",
        str(src),
        str(dst),
    ]]


def test_pdf_to_txt_uses_pdftotext(tmp_path):
    src = tmp_path / "contract.pdf"
    dst = tmp_path / "contract.txt"

    commands, warnings = build_pdf_commands(src, dst, "txt", PdfAdvancedOptions())

    assert warnings == []
    assert commands == [["pdftotext", str(src), str(dst)]]


def test_pdf_to_html_uses_pdftohtml(tmp_path):
    src = tmp_path / "contract.pdf"
    dst = tmp_path / "contract.html"

    commands, warnings = build_pdf_commands(src, dst, "html", PdfAdvancedOptions(strip_metadata=True))

    assert "Remoção de metadados" in warnings[0]
    assert commands == [["pdftohtml", "-s", "-noframes", str(src), str(dst)]]


def test_pdf_to_png_uses_selected_dpi(tmp_path):
    src = tmp_path / "contract.pdf"
    dst = tmp_path / "page.png"

    commands, warnings = build_pdf_commands(src, dst, "png", PdfAdvancedOptions(dpi=300))

    assert warnings == []
    assert commands == [["pdftoppm", "-singlefile", "-r", "300", "-png", str(src), str(dst.with_suffix(""))]]


def test_pdf_ocr_builds_ocrmypdf_command(tmp_path):
    src = tmp_path / "scan.pdf"
    dst = tmp_path / "scan.pdf"
    options = PdfAdvancedOptions(ocr=True, ocr_language="por", searchable_pdf=True)

    commands, warnings = build_pdf_commands(src, dst, "pdf", options)

    assert warnings == []
    assert commands == [["ocrmypdf", "-l", "por", str(src), str(dst)]]


def test_editable_document_to_pdf_applies_quality_and_toc(tmp_path):
    src = tmp_path / "report.docx"
    dst = tmp_path / "report.pdf"
    options = DocumentAdvancedOptions(pdf_quality="print", generate_toc=True)

    commands, warnings = build_editable_document_commands(src, dst, "pdf", options)

    assert warnings == []
    assert commands == [[
        "pandoc",
        str(src),
        "-o",
        str(dst),
        "--pdf-engine-opt=-dPDFSETTINGS=/prepress",
        "--toc",
    ]]


def test_editable_document_to_md_applies_markdown_options(tmp_path):
    src = tmp_path / "report.docx"
    dst = tmp_path / "report.md"
    options = DocumentAdvancedOptions(
        extract_text_only=True,
        include_images=False,
        output_mode="folder",
        encoding="latin1",
        markdown_flavor="commonmark",
        generate_toc=True,
        strip_metadata=True,
    )

    commands, warnings = build_editable_document_commands(src, dst, "md", options)

    assert "Remoção de imagens" in warnings[0]
    assert "Remoção de metadados" in warnings[1]
    assert commands == [[
        "pandoc",
        str(src),
        "-o",
        str(dst),
        "-t",
        "commonmark",
        "-t",
        "plain",
        "--extract-media",
        str(dst.with_suffix("")),
        "--metadata",
        "charset=latin1",
        "--toc",
    ]]


def test_convert_document_runs_command(tmp_path, mocker):
    src = tmp_path / "report.docx"
    dst = tmp_path / "report.pdf"
    src.touch()
    mock_run = mocker.patch("subprocess.run", return_value=MagicMock(returncode=0, stderr=""))

    assert convert_document(str(src), "pdf", str(dst), document_options=DocumentAdvancedOptions()) == str(dst)
    assert mock_run.call_args[0][0][:4] == ["pandoc", str(src), "-o", str(dst)]


def test_convert_document_reports_missing_pandoc(tmp_path, mocker):
    src = tmp_path / "report.docx"
    dst = tmp_path / "report.pdf"
    src.touch()
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)

    with pytest.raises(RuntimeError, match="Pandoc não está instalado"):
        convert_document(str(src), "pdf", str(dst), document_options=DocumentAdvancedOptions())


def test_convert_document_reports_missing_pdftohtml(tmp_path, mocker):
    src = tmp_path / "contract.pdf"
    dst = tmp_path / "contract.html"
    src.touch()
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)

    with pytest.raises(RuntimeError, match="Poppler não está instalado"):
        convert_document(str(src), "html", str(dst), pdf_options=PdfAdvancedOptions())
