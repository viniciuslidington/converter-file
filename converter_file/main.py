# converter_file/main.py
import argparse
import glob
import sys
from pathlib import Path

from converter_file.detect import detect_group
from converter_file.menu import prompt_target_format
from converter_file.convert_image import convert_image
from converter_file.convert_media import convert_media


def _convert_single(file_path: str, target_format: str | None = None) -> bool:
    try:
        group = detect_group(file_path)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return False

    if target_format is None:
        target_format = prompt_target_format(group)

    try:
        if group == "image":
            output = convert_image(file_path, target_format)
        else:
            output = convert_media(file_path, target_format)
        print(f"Convertido: {output}")
        return True
    except (FileExistsError, FileNotFoundError, RuntimeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return False


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

    any_error = False

    if len(files) == 1:
        if not _convert_single(files[0]):
            any_error = True
    else:
        # Batch mode: collect unique groups from all valid files first
        valid_groups: set[str] = set()
        for f in files:
            try:
                valid_groups.add(detect_group(f))
            except ValueError:
                pass  # per-file error handled inside _convert_single

        if not valid_groups:
            print("Nenhum arquivo suportado encontrado.", file=sys.stderr)
            any_error = True
        elif len(valid_groups) > 1:
            print(
                "Erro: o lote contém arquivos de grupos de formato diferentes "
                f"({', '.join(sorted(valid_groups))}). "
                "Converta cada grupo separadamente.",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            group = next(iter(valid_groups))
            target_format = prompt_target_format(group)
            for f in files:
                if not _convert_single(f, target_format):
                    any_error = True

    if any_error:
        sys.exit(1)
