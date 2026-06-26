import argparse
import glob
import platform
import subprocess
import sys
from pathlib import Path

from converter_file.detect import detect_group
from converter_file.menu import prompt_target_format
from converter_file.convert_image import convert_image
from converter_file.convert_media import convert_media

_IS_MACOS = platform.system() == "Darwin"


# ── File / folder dialogs ────────────────────────────────────────────────────

def _pick_files() -> list[str]:
    if _IS_MACOS:
        return _osascript_pick_files()
    return _tkinter_pick_files()


def _pick_save_file(suggested_name: str) -> str | None:
    if _IS_MACOS:
        return _osascript_save_file(suggested_name)
    return _tkinter_save_file(suggested_name)


def _pick_save_folder() -> str | None:
    if _IS_MACOS:
        return _osascript_save_folder()
    return _tkinter_save_folder()


# ── macOS (osascript) ────────────────────────────────────────────────────────

def _osascript_pick_files() -> list[str]:
    script = """
set theFiles to choose file ¬
    with prompt "Escolha arquivo(s) para converter:" ¬
    with multiple selections allowed
set output to ""
repeat with f in theFiles
    set output to output & POSIX path of f & linefeed
end repeat
return output
"""
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return [p for p in result.stdout.strip().splitlines() if p]


def _osascript_save_file(suggested_name: str) -> str | None:
    script = f'POSIX path of (choose file name with prompt "Salvar como:" default name "{suggested_name}")'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _osascript_save_folder() -> str | None:
    script = 'POSIX path of (choose folder with prompt "Escolha a pasta de destino:")'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


# ── Linux / Windows (tkinter) ────────────────────────────────────────────────

def _tk_root():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        return root
    except ImportError:
        print(
            "Erro: tkinter não encontrado.\n"
            "  Linux: sudo apt install python3-tk  (ou dnf / pacman equivalente)\n"
            "  Windows: reinstale o Python marcando a opção tcl/tk.",
            file=sys.stderr,
        )
        sys.exit(1)


def _tkinter_pick_files() -> list[str]:
    from tkinter import filedialog
    root = _tk_root()
    files = filedialog.askopenfilenames(title="Escolha arquivo(s) para converter:")
    root.destroy()
    return list(files)


def _tkinter_save_file(suggested_name: str) -> str | None:
    from tkinter import filedialog
    root = _tk_root()
    path = filedialog.asksaveasfilename(title="Salvar como:", initialfile=suggested_name)
    root.destroy()
    return path or None


def _tkinter_save_folder() -> str | None:
    from tkinter import filedialog
    root = _tk_root()
    folder = filedialog.askdirectory(title="Escolha a pasta de destino:")
    root.destroy()
    return folder or None


# ── Conversion ───────────────────────────────────────────────────────────────

def _convert_single(file_path: str, target_format: str, output_path: str | None = None) -> bool:
    try:
        group = detect_group(file_path)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return False

    try:
        if group == "image":
            output = convert_image(file_path, target_format, output_path)
        else:
            output = convert_media(file_path, target_format, output_path)
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


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="convert-file",
        description="Converte arquivos de vídeo, áudio e imagem.",
    )
    parser.add_argument(
        "inputs", nargs="*", metavar="arquivo",
        help="Arquivo(s) ou pasta para converter (omita para abrir seletor de arquivo)",
    )
    args = parser.parse_args()

    if not args.inputs:
        picked = _pick_files()
        if not picked:
            print("Nenhum arquivo selecionado.", file=sys.stderr)
            sys.exit(1)
        files = picked
    else:
        files = _collect_files(args.inputs)

    any_error = False

    if len(files) == 1:
        file = files[0]
        try:
            group = detect_group(file)
        except (ValueError, FileNotFoundError, RuntimeError) as e:
            print(f"Erro: {e}", file=sys.stderr)
            sys.exit(1)

        target_format = prompt_target_format(group)

        suggested = Path(file).stem + "." + target_format
        output_path = _pick_save_file(suggested)
        if output_path is None:
            print("Destino não selecionado.", file=sys.stderr)
            sys.exit(1)

        if not _convert_single(file, target_format, output_path):
            any_error = True

    else:
        valid_groups: set[str] = set()
        for f in files:
            try:
                valid_groups.add(detect_group(f))
            except ValueError:
                pass

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

            save_folder = _pick_save_folder()
            if save_folder is None:
                print("Destino não selecionado.", file=sys.stderr)
                sys.exit(1)

            for f in files:
                out = str(Path(save_folder) / (Path(f).stem + f".{target_format}"))
                if not _convert_single(f, target_format, out):
                    any_error = True

    if any_error:
        sys.exit(1)
