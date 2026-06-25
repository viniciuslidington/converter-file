# Converter File — Glossary

## Termos do domínio

**Input File**
Arquivo fornecido pelo usuário para conversão. Pode ser vídeo, áudio ou imagem. O tipo é detectado pela extensão.

**Target Format**
Formato de destino escolhido pelo usuário via menu interativo após a detecção do tipo do Input File.

**Output File**
Arquivo gerado após a conversão. Salvo na mesma pasta do Input File, com o mesmo nome e extensão do Target Format.

**Conversion Engine**
Backend responsável pela conversão. `ffmpeg` para vídeo e áudio; `Pillow` para imagens.

**Format Group**
Categoria do arquivo: `video`, `audio`, ou `image`. Determina quais Target Formats são oferecidos e qual Conversion Engine é usado.

**Batch Mode**
Modo em que múltiplos Input Files (via glob ou pasta) são processados sequencialmente com o mesmo Target Format.

## Formatos suportados por Format Group

| Format Group | Extensões de entrada e saída |
|---|---|
| video | .mov, .mp4, .avi, .mkv, .webm |
| audio | .mp3, .wav, .aac, .flac, .ogg |
| image | .jpg, .png, .webp, .gif, .bmp, .tiff |
