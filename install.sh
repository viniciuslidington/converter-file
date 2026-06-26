#!/bin/bash
set -e

OS="$(uname -s)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Instalando converter-file..."
echo "    Sistema: $OS"
echo ""

# ── macOS ────────────────────────────────────────────────────────────────────
if [[ "$OS" == "Darwin" ]]; then

    if ! command -v brew &>/dev/null; then
        echo "==> Instalando Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
    else
        echo "✓ Homebrew já instalado"
    fi

    if ! command -v python3.11 &>/dev/null; then
        echo "==> Instalando Python 3.11..."
        brew install python@3.11
    else
        echo "✓ Python 3.11 já instalado"
    fi

    if ! command -v ffmpeg &>/dev/null; then
        echo "==> Instalando ffmpeg..."
        brew install ffmpeg
    else
        echo "✓ ffmpeg já instalado"
    fi

    PYTHON=python3.11

    # PATH no ~/.zshrc
    BREW_BIN="/opt/homebrew/bin"
    if [[ ":$PATH:" != *":$BREW_BIN:"* ]]; then
        SHELL_RC="$HOME/.zshrc"
        if ! grep -q 'opt/homebrew/bin' "$SHELL_RC" 2>/dev/null; then
            echo "==> Adicionando Homebrew ao PATH em $SHELL_RC..."
            echo 'export PATH="/opt/homebrew/bin:$PATH"' >> "$SHELL_RC"
            RELOAD_MSG="source ~/.zshrc"
        fi
    fi

# ── Linux ────────────────────────────────────────────────────────────────────
elif [[ "$OS" == "Linux" ]]; then

    if command -v apt &>/dev/null; then
        echo "==> Instalando dependências (apt)..."
        sudo apt update -qq
        sudo apt install -y python3.11 python3.11-venv python3-pip python3-tk ffmpeg
    elif command -v dnf &>/dev/null; then
        echo "==> Instalando dependências (dnf)..."
        sudo dnf install -y python3.11 python3-pip python3-tkinter ffmpeg
    elif command -v pacman &>/dev/null; then
        echo "==> Instalando dependências (pacman)..."
        sudo pacman -S --noconfirm python python-pip tk ffmpeg
    else
        echo "Erro: gerenciador de pacotes não reconhecido."
        echo "Instale manualmente: python3.11, python3-tk, ffmpeg"
        exit 1
    fi

    PYTHON=python3.11
    RELOAD_MSG="source ~/.bashrc"

else
    echo "Erro: sistema operacional '$OS' não suportado por este script."
    echo "No Windows use: install.ps1"
    exit 1
fi

# ── Pacote Python (comum) ────────────────────────────────────────────────────
echo "==> Instalando pacote converter-file..."
"$PYTHON" -m pip install -e "$SCRIPT_DIR" -q

echo ""
echo "✓ Instalação concluída!"
echo ""
echo "  Use o comando:  convert-file"
if [[ -n "${RELOAD_MSG:-}" ]]; then
    echo ""
    echo "  Se o comando não for encontrado, rode:"
    echo "    $RELOAD_MSG"
fi
