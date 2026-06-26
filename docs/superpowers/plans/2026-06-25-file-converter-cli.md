# File Converter CLI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CLI em Python que converte arquivos de vídeo, áudio e imagem para formatos alternativos, com menu interativo e modo batch.

**Architecture:** Um pacote Python `converter_file` com módulos separados para detecção de formato, menu interativo, e dois engines de conversão (ffmpeg via subprocess para mídia, Pillow para imagens). O ponto de entrada `main.py` orquestra o fluxo: detectar → menu → converter, com suporte a batch via glob/pasta.

**Tech Stack:** Python 3.11+, Pillow (imagens), ffmpeg (binário externo, chamado via subprocess), pytest + pytest-mock (testes).

## Global Constraints

- Python 3.11+
- Sem frameworks de CLI externos (typer, click) — apenas `argparse` + `input()`
- ffmpeg deve estar instalado no sistema (`ffmpeg` no PATH)
- Output salvo na mesma pasta do Input File, mesmo nome base, nova extensão
- Sem sobrescrever arquivos existentes — abortar com mensagem de erro clara
- Formatos suportados exatamente como definidos no CONTEXT.md

---

## File Structure

```
converter_file/
├── pyproject.toml              # metadata e dependências do pacote
├── requirements-dev.txt        # pytest, pytest-mock
├── converter_file/
│   ├── __init__.py
│   ├── detect.py               # detecta Format Group a partir da extensão
│   ├── menu.py                 # menu interativo para escolher Target Format
│   ├── convert_image.py        # converte imagens via Pillow
│   ├── convert_media.py        # converte vídeo/áudio via ffmpeg subprocess
│   └── main.py                 # CLI entry point + batch orchestration
└── tests/
    ├── __init__.py
    ├── test_detect.py
    ├── test_menu.py
    ├── test_convert_image.py
    ├── test_convert_media.py
    └── test_main.py
```

---

### Task 1: Scaffold do projeto

**Files:**

- Create: `pyproject.toml`
- Create: `requirements-dev.txt`
- Create: `converter_file/__init__.py`
- Create: `tests/__init__.py`

**Interfaces:**

- Produces: pacote instalável `converter_file`, comando `convert-file` no PATH

- [ ] **Step 1: Criar pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "converter-file"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["Pillow>=10.0"]

[project.scripts]
convert-file = "converter_file.main:main"
```

- [ ] **Step 2: Criar requirements-dev.txt**

```
pytest>=8.0
pytest-mock>=3.12
```

- [ ] **Step 3: Criar converter_file/__init__.py vazio**

```python
```

- [ ] **Step 4: Criar tests/__init__.py vazio**

```python
```

- [ ] **Step 5: Instalar pacote em modo editável**

```bash
pip install -e ".[dev]" 2>/dev/null || pip install -e . && pip install -r requirements-dev.txt
```

Expected: pacote instalado sem erros.

- [ ] **Step 6: Inicializar git e commitar scaffold**

```bash
git init
git add pyproject.toml requirements-dev.txt converter_file/__init__.py tests/__init__.py
git commit -m "chore: project scaffold"
```

---

### Task 2: Detecção de Format Group (`detect.py`)

**Files:**

- Create: `converter_file/detect.py`
- Test: `tests/test_detect.py`

**Interfaces:**

- Produces:
  - `detect_group(path: str) -> str` — retorna `"video"`, `"audio"`, ou `"image"`; levanta `ValueError` se extensão não suportada
  - `SUPPORTED_FORMATS: dict[str, list[str]]` — mapa `{group: [extensões sem ponto]}`

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/test_detect.py
import pytest
from converter_file.detect import detect_group, SUPPORTED_FORMATS

def test_video_extensions():
    for ext in ["mov", "mp4", "avi", "mkv", "webm"]:
        assert detect_group(f"file.{ext}") == "video"

def test_audio_extensions():
    for ext in ["mp3", "wav", "aac", "flac", "ogg"]:
        assert detect_group(f"file.{ext}") == "audio"

def test_image_extensions():
    for ext in ["jpg", "png", "webp", "gif", "bmp", "tiff"]:
        assert detect_group(f"file.{ext}") == "image"

def test_uppercase_extension():
    assert detect_group("file.MP4") == "video"

def test_unsupported_raises():
    with pytest.raises(ValueError, match="Formato não suportado"):
        detect_group("file.docx")

def test_supported_formats_keys():
    assert set(SUPPORTED_FORMATS.keys()) == {"video", "audio", "image"}
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_detect.py -v
```

Expected: `ModuleNotFoundError` ou `ImportError` — módulo não existe ainda.

- [ ] **Step 3: Implementar detect.py**

```python
# converter_file/detect.py
SUPPORTED_FORMATS: dict[str, list[str]] = {
    "video": ["mov", "mp4", "avi", "mkv", "webm"],
    "audio": ["mp3", "wav", "aac", "flac", "ogg"],
    "image": ["jpg", "png", "webp", "gif", "bmp", "tiff"],
}

_EXT_TO_GROUP: dict[str, str] = {
    ext: group
    for group, exts in SUPPORTED_FORMATS.items()
    for ext in exts
}


def detect_group(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower()
    group = _EXT_TO_GROUP.get(ext)
    if group is None:
        raise ValueError(f"Formato não suportado: .{ext}")
    return group
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_detect.py -v
```

Expected: todos PASS.

- [ ] **Step 5: Commitar**

```bash
git add converter_file/detect.py tests/test_detect.py
git commit -m "feat: format group detection"
```

---

### Task 3: Menu interativo (`menu.py`)

**Files:**

- Create: `converter_file/menu.py`
- Test: `tests/test_menu.py`

**Interfaces:**

- Consumes: `SUPPORTED_FORMATS` de `converter_file.detect`
- Produces:
  - `prompt_target_format(group: str) -> str` — exibe menu numerado, lê `input()`, retorna extensão escolhida (ex.: `"mp4"`); levanta `ValueError` para grupo inválido

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/test_menu.py
import pytest
from unittest.mock import patch
from converter_file.menu import prompt_target_format

def test_valid_video_choice(capsys):
    with patch("builtins.input", return_value="1"):
        result = prompt_target_format("video")
    assert result in ["mov", "mp4", "avi", "mkv", "webm"]

def test_valid_image_choice(capsys):
    with patch("builtins.input", return_value="2"):
        result = prompt_target_format("image")
    assert result in ["jpg", "png", "webp", "gif", "bmp", "tiff"]

def test_invalid_choice_reprompts():
    # primeira resposta inválida, segunda válida
    with patch("builtins.input", side_effect=["99", "1"]):
        result = prompt_target_format("audio")
    assert result in ["mp3", "wav", "aac", "flac", "ogg"]

def test_invalid_group_raises():
    with pytest.raises(ValueError, match="Grupo inválido"):
        prompt_target_format("document")

def test_menu_shows_options(capsys):
    with patch("builtins.input", return_value="1"):
        prompt_target_format("video")
    captured = capsys.readouterr()
    assert "1." in captured.out
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_menu.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implementar menu.py**

```python
# converter_file/menu.py
from converter_file.detect import SUPPORTED_FORMATS


def prompt_target_format(group: str) -> str:
    if group not in SUPPORTED_FORMATS:
        raise ValueError(f"Grupo inválido: {group}")

    options = SUPPORTED_FORMATS[group]

    while True:
        print(f"\nFormatos disponíveis para {group}:")
        for i, fmt in enumerate(options, start=1):
            print(f"  {i}. .{fmt}")

        choice = input("Escolha o número do formato de destino: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]

        print(f"Opção inválida. Digite um número entre 1 e {len(options)}.")
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_menu.py -v
```

Expected: todos PASS.

- [ ] **Step 5: Commitar**

```bash
git add converter_file/menu.py tests/test_menu.py
git commit -m "feat: interactive format menu"
```

---

### Task 4: Conversão de imagens (`convert_image.py`)

**Files:**

- Create: `converter_file/convert_image.py`
- Test: `tests/test_convert_image.py`

**Interfaces:**

- Produces:
  - `convert_image(input_path: str, target_format: str) -> str` — converte e salva o output; retorna caminho do arquivo gerado; levanta `FileExistsError` se output já existe; levanta `FileNotFoundError` se input não existe

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/test_convert_image.py
import pytest
import os
from pathlib import Path
from PIL import Image
from converter_file.convert_image import convert_image


@pytest.fixture
def tmp_png(tmp_path):
    img = Image.new("RGB", (10, 10), color="red")
    path = tmp_path / "test.png"
    img.save(path)
    return str(path)


def test_converts_png_to_jpg(tmp_png, tmp_path):
    result = convert_image(tmp_png, "jpg")
    assert result == str(tmp_path / "test.jpg")
    assert os.path.exists(result)
    img = Image.open(result)
    assert img.format == "JPEG"


def test_converts_png_to_webp(tmp_png, tmp_path):
    result = convert_image(tmp_png, "webp")
    assert result == str(tmp_path / "test.webp")
    assert os.path.exists(result)


def test_raises_if_output_exists(tmp_png, tmp_path):
    (tmp_path / "test.jpg").touch()
    with pytest.raises(FileExistsError, match="já existe"):
        convert_image(tmp_png, "jpg")


def test_raises_if_input_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert_image(str(tmp_path / "nope.png"), "jpg")
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_convert_image.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implementar convert_image.py**

```python
# converter_file/convert_image.py
import os
from pathlib import Path
from PIL import Image

_PILLOW_FORMAT: dict[str, str] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
}


def convert_image(input_path: str, target_format: str) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    dst = src.with_suffix(f".{target_format}")
    if dst.exists():
        raise FileExistsError(f"Arquivo de saída já existe: {dst}")

    pillow_fmt = _PILLOW_FORMAT.get(target_format.lower())
    if pillow_fmt is None:
        raise ValueError(f"Formato de imagem não suportado: {target_format}")

    img = Image.open(src)
    if pillow_fmt == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(dst, format=pillow_fmt)
    return str(dst)
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_convert_image.py -v
```

Expected: todos PASS.

- [ ] **Step 5: Commitar**

```bash
git add converter_file/convert_image.py tests/test_convert_image.py
git commit -m "feat: image conversion via Pillow"
```

---

### Task 5: Conversão de vídeo/áudio (`convert_media.py`)

**Files:**

- Create: `converter_file/convert_media.py`
- Test: `tests/test_convert_media.py`

**Interfaces:**

- Produces:
  - `convert_media(input_path: str, target_format: str) -> str` — chama ffmpeg via subprocess; retorna caminho do output; levanta `FileExistsError` se output já existe; levanta `FileNotFoundError` se input não existe; levanta `RuntimeError` com stderr do ffmpeg em caso de falha

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/test_convert_media.py
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
from converter_file.convert_media import convert_media


def test_raises_if_input_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert_media(str(tmp_path / "nope.mp4"), "avi")


def test_raises_if_output_exists(tmp_path):
    src = tmp_path / "video.mp4"
    src.touch()
    dst = tmp_path / "video.avi"
    dst.touch()
    with pytest.raises(FileExistsError, match="já existe"):
        convert_media(str(src), "avi")


def test_calls_ffmpeg_with_correct_args(tmp_path, mocker):
    src = tmp_path / "video.mp4"
    src.touch()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0, stderr="")

    result = convert_media(str(src), "avi")

    assert result == str(tmp_path / "video.avi")
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "ffmpeg"
    assert str(src) in call_args
    assert str(tmp_path / "video.avi") in call_args


def test_raises_on_ffmpeg_failure(tmp_path, mocker):
    src = tmp_path / "video.mp4"
    src.touch()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=1, stderr="ffmpeg error details")

    with pytest.raises(RuntimeError, match="ffmpeg error details"):
        convert_media(str(src), "avi")
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_convert_media.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implementar convert_media.py**

```python
# converter_file/convert_media.py
import subprocess
from pathlib import Path


def convert_media(input_path: str, target_format: str) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    dst = src.with_suffix(f".{target_format}")
    if dst.exists():
        raise FileExistsError(f"Arquivo de saída já existe: {dst}")

    result = subprocess.run(
        ["ffmpeg", "-i", str(src), str(dst)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return str(dst)
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_convert_media.py -v
```

Expected: todos PASS.

- [ ] **Step 5: Commitar**

```bash
git add converter_file/convert_media.py tests/test_convert_media.py
git commit -m "feat: video/audio conversion via ffmpeg"
```

---

### Task 6: Orquestração e CLI principal (`main.py`)

**Files:**

- Create: `converter_file/main.py`
- Test: `tests/test_main.py`

**Interfaces:**

- Consumes:
  - `detect_group(path: str) -> str` de `converter_file.detect`
  - `prompt_target_format(group: str) -> str` de `converter_file.menu`
  - `convert_image(input_path: str, target_format: str) -> str` de `converter_file.convert_image`
  - `convert_media(input_path: str, target_format: str) -> str` de `converter_file.convert_media`
- Produces:
  - `main()` — entry point chamado pelo comando `convert-file`
  - Argumento posicional: um ou mais caminhos (ou glob) de Input Files
  - Flag `--batch` (ou passagem de diretório) para Batch Mode

**CLI usage:**

```
convert-file arquivo.mp4
convert-file imagens/*.png
convert-file pasta/
```

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/test_main.py
import pytest
from unittest.mock import patch, call
from converter_file.main import main


def test_single_file_conversion(mocker, tmp_path):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value=str(tmp_path / "clip.avi"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    mock_convert.assert_called_once_with(str(src), "avi")


def test_single_image_conversion(mocker, tmp_path):
    src = tmp_path / "photo.png"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="image")
    mocker.patch("converter_file.main.prompt_target_format", return_value="jpg")
    mock_convert = mocker.patch("converter_file.main.convert_image", return_value=str(tmp_path / "photo.jpg"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    mock_convert.assert_called_once_with(str(src), "jpg")


def test_batch_directory(mocker, tmp_path):
    (tmp_path / "a.mp4").touch()
    (tmp_path / "b.mp4").touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mock_convert = mocker.patch("converter_file.main.convert_media", return_value="out.avi")

    with patch("sys.argv", ["convert-file", str(tmp_path)]):
        main()

    assert mock_convert.call_count == 2


def test_unsupported_format_prints_error(mocker, tmp_path, capsys):
    src = tmp_path / "doc.pdf"
    src.touch()

    mocker.patch("converter_file.main.detect_group", side_effect=ValueError("Formato não suportado: .pdf"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    captured = capsys.readouterr()
    assert "Formato não suportado" in captured.out or "Formato não suportado" in captured.err


def test_output_exists_prints_error(mocker, tmp_path, capsys):
    src = tmp_path / "clip.mp4"
    src.touch()

    mocker.patch("converter_file.main.detect_group", return_value="video")
    mocker.patch("converter_file.main.prompt_target_format", return_value="avi")
    mocker.patch("converter_file.main.convert_media", side_effect=FileExistsError("já existe"))

    with patch("sys.argv", ["convert-file", str(src)]):
        main()

    captured = capsys.readouterr()
    assert "já existe" in captured.out or "já existe" in captured.err
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implementar main.py**

```python
# converter_file/main.py
import argparse
import sys
from pathlib import Path

from converter_file.detect import detect_group
from converter_file.menu import prompt_target_format
from converter_file.convert_image import convert_image
from converter_file.convert_media import convert_media


def _convert_single(file_path: str, target_format: str | None = None) -> None:
    try:
        group = detect_group(file_path)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return

    if target_format is None:
        target_format = prompt_target_format(group)

    try:
        if group == "image":
            output = convert_image(file_path, target_format)
        else:
            output = convert_media(file_path, target_format)
        print(f"Convertido: {output}")
    except (FileExistsError, FileNotFoundError, RuntimeError) as e:
        print(f"Erro: {e}", file=sys.stderr)


def _collect_files(inputs: list[str]) -> list[str]:
    files = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            files.extend(str(f) for f in p.iterdir() if f.is_file())
        else:
            files.append(item)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="convert-file",
        description="Converte arquivos de vídeo, áudio e imagem.",
    )
    parser.add_argument("inputs", nargs="+", metavar="arquivo", help="Arquivo(s) ou pasta para converter")
    args = parser.parse_args()

    files = _collect_files(args.inputs)

    if len(files) == 1:
        _convert_single(files[0])
        return

    # Batch mode: pede formato uma vez, aplica a todos
    first_valid_group = None
    for f in files:
        try:
            first_valid_group = detect_group(f)
            break
        except ValueError:
            continue

    if first_valid_group is None:
        print("Nenhum arquivo suportado encontrado.", file=sys.stderr)
        return

    target_format = prompt_target_format(first_valid_group)

    for f in files:
        _convert_single(f, target_format)
```

- [ ] **Step 4: Rodar todos os testes**

```bash
pytest tests/ -v
```

Expected: todos PASS.

- [ ] **Step 5: Commitar**

```bash
git add converter_file/main.py tests/test_main.py
git commit -m "feat: CLI entry point and batch mode"
```

---

### Task 7: Smoke test manual

- [ ] **Step 1: Instalar e verificar comando**

```bash
pip install -e .
convert-file --help
```

Expected: help text com `arquivo` listado como argumento.

- [ ] **Step 2: Testar conversão de imagem (se tiver uma imagem disponível)**

```bash
convert-file /path/to/any/image.png
# Escolher "jpg" no menu
```

Expected: `Convertido: /path/to/any/image.jpg` e arquivo criado.

- [ ] **Step 3: Testar erro de formato não suportado**

```bash
touch /tmp/teste.docx
convert-file /tmp/teste.docx
```

Expected: mensagem de erro no stderr, sem crash.

- [ ] **Step 4: Commitar tag de release**

```bash
git tag v0.1.0
```

---

## Self-Review

**Spec coverage:**

| Requisito (CONTEXT.md)                            | Task que implementa           |
| ------------------------------------------------- | ----------------------------- |
| Input File detectado pela extensão               | Task 2 (`detect.py`)        |
| Menu interativo para Target Format                | Task 3 (`menu.py`)          |
| Output na mesma pasta, mesmo nome, nova extensão | Tasks 4 e 5                   |
| Engine ffmpeg para vídeo/áudio                  | Task 5 (`convert_media.py`) |
| Engine Pillow para imagens                        | Task 4 (`convert_image.py`) |
| Batch Mode (glob/pasta)                           | Task 6 (`main.py`)          |
| Todos os formatos do CONTEXT.md                   | Tasks 2, 3, 4, 5              |

Nenhuma lacuna identificada.

**Placeholder scan:** Nenhum TBD, TODO, ou "similar to Task N" encontrado.

**Type consistency:** `detect_group`, `prompt_target_format`, `convert_image`, `convert_media` — nomes usados consistentemente em todos os tasks.
