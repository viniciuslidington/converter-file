# converter-file

CLI em Python para converter arquivos de vídeo, áudio e imagem para formatos alternativos.

## Requisitos

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/download.html) instalado e disponível no PATH (para vídeo e áudio)

## Instalação

```bash
pip install -e .
```

## Uso

```bash
convert-file arquivo.mp4
```

Após detectar o tipo do arquivo, um menu interativo exibe os formatos disponíveis:

```
Formatos disponíveis para video:
  1. .mov
  2. .mp4
  3. .avi
  4. .mkv
  5. .webm
Escolha o número do formato de destino:
```

O arquivo convertido é salvo na mesma pasta com o mesmo nome e a nova extensão.

### Modo batch

Passe uma pasta ou glob — o formato é escolhido uma única vez e aplicado a todos os arquivos:

```bash
convert-file pasta/
convert-file "imagens/*.png"
```

Todos os arquivos do lote devem ser do mesmo tipo (vídeo, áudio ou imagem).

## Formatos suportados

| Tipo   | Formatos                          |
|--------|-----------------------------------|
| Vídeo  | `.mov` `.mp4` `.avi` `.mkv` `.webm` |
| Áudio  | `.mp3` `.wav` `.aac` `.flac` `.ogg` |
| Imagem | `.jpg` `.png` `.webp` `.gif` `.bmp` `.tiff` |

## Desenvolvimento

```bash
pip install -e .
pip install -r requirements-dev.txt
pytest
```
