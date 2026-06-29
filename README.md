# converter-file

CLI em Python para converter arquivos de vídeo, áudio e imagem para formatos alternativos.


## Requisitos

- Python 3.11+
- ffmpeg (para conversão de vídeo e áudio)

## Instalação

Clone o repositório e execute o script correspondente ao seu sistema:

**macOS / Linux**
```bash
git clone https://github.com/viniciuslidington/converter-file.git
cd converter-file
./install.sh
```

**Windows** (PowerShell como Administrador)
```powershell
git clone https://github.com/viniciuslidington/converter-file.git
cd converter-file
.\install.ps1
```

Os scripts instalam automaticamente o Python 3.11, o ffmpeg e o pacote.

## Uso

### Arquivo único

```bash
convert-file              # abre seletor de arquivo nativo
convert-file video.mp4    # ou passe o caminho direto
```

Fluxo completo:

1. Seletor de arquivo nativo do macOS (se sem argumento)
2. Menu no terminal para escolher o formato de destino, vendo o tamanho estimado de cada opção
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

1. Formato de destino escolhido uma única vez no terminal, vendo o tamanho total estimado do lote
2. Seletor de **pasta de destino** nativo — todos os arquivos convertidos são salvos lá
3. Nomes originais são preservados, apenas a extensão muda

Todos os arquivos do lote devem ser do mesmo tipo (vídeo, áudio ou imagem).

## Formatos suportados

| Tipo   | Formatos                                                |
| ------ | ------------------------------------------------------- |
| Vídeo | `.mov` `.mp4` `.avi` `.mkv` `.webm`           |
| Áudio | `.mp3` `.wav` `.aac` `.flac` `.ogg`           |
| Imagem | `.jpg` `.png` `.webp` `.gif` `.bmp` `.tiff` |

Ao converter um vídeo, o menu também oferece formatos de áudio (`.mp3`,
`.wav`, `.aac`, `.flac`, `.ogg`) para extrair somente a trilha sonora.

## Desenvolvimento

```bash
pip install -e .
pip install -r requirements-dev.txt
pytest
```
