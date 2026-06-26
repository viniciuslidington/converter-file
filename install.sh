#!/bin/bash
set -e

echo "==> Instalando converter-file..."

# Homebrew
if ! command -v brew &>/dev/null; then
    echo "==> Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Adiciona brew ao PATH para o resto do script
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
else
    echo "✓ Homebrew já instalado"
fi

# Python 3.11
if ! command -v python3.11 &>/dev/null; then
    echo "==> Instalando Python 3.11..."
    brew install python@3.11
else
    echo "✓ Python 3.11 já instalado"
fi

# ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "==> Instalando ffmpeg..."
    brew install ffmpeg
else
    echo "✓ ffmpeg já instalado"
fi

# Pacote Python
echo "==> Instalando converter-file..."
python3.11 -m pip install -e "$(dirname "$0")" -q

# PATH no ~/.zshrc
BREW_BIN="/opt/homebrew/bin"
if [[ ":$PATH:" != *":$BREW_BIN:"* ]]; then
    SHELL_RC="$HOME/.zshrc"
    if ! grep -q 'opt/homebrew/bin' "$SHELL_RC" 2>/dev/null; then
        echo "==> Adicionando Homebrew ao PATH em $SHELL_RC..."
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> "$SHELL_RC"
        echo "    Reinicie o terminal ou rode: source $SHELL_RC"
    fi
fi

echo ""
echo "✓ Instalação concluída!"
echo ""
echo "  Use o comando:  convert-file"
echo ""
echo "  Se o comando não for encontrado, rode:"
echo "    source ~/.zshrc"
