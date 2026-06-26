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

### Arquivo único

```bash
convert-file              # abre seletor de arquivo nativo
convert-file video.mp4    # ou passe o caminho direto
```

Fluxo completo:

1. Seletor de arquivo nativo do macOS (se sem argumento)
2. Menu no terminal para escolher o formato de destino
3. Seletor **"Salvar como"** nativo — escolha o nome e a pasta de destino
4. Arquivo convertido e salvo no local escolhido

### Modo batch

Passe uma pasta, múltiplos arquivos ou um glob:

```bash
convert-file pasta/
convert-file clip1.mp4 clip2.mp4
convert-file "imagens/*.png"
```

Fluxo batch:

1. Formato de destino escolhido uma única vez no terminal
2. Seletor de **pasta de destino** nativo — todos os arquivos convertidos são salvos lá
3. Nomes originais são preservados, apenas a extensão muda

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
