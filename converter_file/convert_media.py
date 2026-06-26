import subprocess
from pathlib import Path


def convert_media(input_path: str, target_format: str, output_path: str | None = None) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    dst = Path(output_path) if output_path else src.with_suffix(f".{target_format}")
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
