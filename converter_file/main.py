# converter_file/main.py
import argparse
import glob
import sys
from pathlib import Path

from converter_file.detect import detect_group
from converter_file.menu import prompt_target_format
from converter_file.convert_image import convert_image
from converter_file.convert_media import convert_media


def _convert_single(file_path: str, target_format: str | None = None) -> None:
    try:
        group = detect_group(file_path)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
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
        elif p.is_file():
            files.append(item)
        else:
            matches = glob.glob(item)
            if matches:
                files.extend(matches)
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
