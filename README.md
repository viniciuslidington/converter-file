# converter-file

CLI em Python para converter arquivos de vídeo, áudio e imagem para formatos alternativos.

## Requisitos

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/download.html) instalado e disponível no PATH (para vídeo e áudio)

## Instalação

**1. Instalar o ffmpeg** (necessário para vídeo e áudio):

```bash
brew install ffmpeg
```

**2. Instalar o pacote:**

```bash
pip install -e .
```

## Uso

### Seletor de arquivo (sem argumentos)

```bash
convert-file
```

Abre o seletor de arquivo nativo do macOS. Selecione um ou mais arquivos e clique em **Escolher**.

### Via terminal

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

Passe uma pasta, múltiplos arquivos ou um glob — o formato é escolhido uma única vez e aplicado a todos:

```bash
convert-file pasta/
convert-file clip1.mp4 clip2.mp4
convert-file "imagens/*.png"
```

Todos os arquivos do lote devem ser do mesmo tipo (vídeo, áudio ou imagem).

## Formatos suportados

| Tipo   | Formatos                                                |
| ------ | ------------------------------------------------------- |
| Vídeo | `.mov` `.mp4` `.avi` `.mkv` `.webm`           |
| Áudio | `.mp3` `.wav` `.aac` `.flac` `.ogg`           |
| Imagem | `.jpg` `.png` `.webp` `.gif` `.bmp` `.tiff` |

## Desenvolvimento

```bash
pip install -e .
pip install -r requirements-dev.txt
pytest
```
