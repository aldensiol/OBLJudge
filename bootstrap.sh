#!/bin/bash

echo "🚀 Starting bootstrap..."

detect_os() {
    case "$(uname -s)" in
        Darwin*)    OS="mac";;
        MINGW*)     OS="windows";;
        CYGWIN*)    OS="windows";;
        MSYS*)      OS="windows";;
        Linux*)     OS="linux";;
        *)          OS="unknown";;
    esac
}

install_dependencies() {
    case $OS in
        "linux")
            # check if basic tools are already installed
            if command -v git &> /dev/null && command -v curl &> /dev/null; then
                echo "✅ Dependencies already installed"
            else
                echo "📦 Installing Linux dependencies..."
                sudo apt-get update
                sudo apt-get install -y build-essential git curl
            fi
            ;;
        "mac")
            if ! command -v brew &> /dev/null; then
                echo "📦 Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            # check if git and curl are installed
            if command -v git &> /dev/null && command -v curl &> /dev/null; then
                echo "✅ Dependencies already installed"
            else
                echo "📦 Installing dependencies via Homebrew..."
                brew install git curl
            fi
            ;;
        "windows")
            echo "📦 Windows detected - assuming dependencies are available"
            ;;
    esac
}

install_uv() {
    if command -v uv &> /dev/null; then
        echo "✅ uv is already installed ($(uv --version))"
    else
        echo "📦 Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # add uv to path for current session
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
}
detect_os
install_dependencies
install_uv
if [ -d ".venv" ] && [ -f "uv.lock" ]; then
    echo "✅ Virtual environment exists, checking sync..."
    uv sync
else
    echo "🔄 Creating virtual environment and syncing dependencies..."
    uv sync
fi

# activate virtual environment
case $OS in
    "windows")
        source .venv/Scripts/activate
        ;;
    *)
        source .venv/bin/activate
        ;;
esac

echo "✅ Bootstrap completed!"