#!/usr/bin/env bash

set -euo pipefail 
# --- Configuration ---
APP_NAME="configurator"
ENTRY_POINT="main.py"
OUTPUT_DIR="dist"
BUILD_VENV="venv"

# --- Helper Functions ---
check_environment() {
    echo "🔍 Checking environment..."
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: python3 could not be found. Please install it to continue."
        exit 1
    fi
    echo "✅ Environment check passed (OS: $(uname -s))."
}

setup_venv() {
    echo "📦 Creating temporary build virtual environment..."
    rm -rf "$BUILD_VENV"
    python3 -m venv "$BUILD_VENV"
    source "$BUILD_VENV/bin/activate"
}

install_dependencies() {
    echo "⬇️  Installing dependencies..."
    python3 -m pip install --upgrade pip
    # add pyinstaller for windows
    python3 -m pip install -r ./requirements.txt
}

install_dependencies_win() {
    echo "⬇️  Installing dependencies..."
    python3 -m pip install --upgrade pip
    # add pyinstaller for windows
    python3 -m pip install -r ./requirementswin.txt
}

compile_app() {
    echo "🔨 Compiling $APP_NAME..."
    pyinstaller --noconfirm --onefile --clean \
        --name "$APP_NAME" \
        --collect-all textual \
        --collect-all rich \
        "$ENTRY_POINT"
}

create_wrapper() {
  [ ! -d "venv" ] && return 1 || echo "Installing dependencies...." 
  source venv/bin/activate
  echo "✅ Dependencies installed."
  echo "🚀 Creating launcher script..."
  cat << 'EOF' > cfg 
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
export PATH="$SCRIPT_DIR/venv/bin:$PATH"
python3 "$SCRIPT_DIR/main.py" "$@"
EOF
  chmod +x cfg
  echo "now you can run ./cfg"
}

run_app_in_venv() {
    echo "▶️ Running application in Venv (Testing Mode)..."
    if python "$ENTRY_POINT"; then
        echo "✅ Application ran successfully in venv."
    else
        echo "⚠️ Warning: Application execution failed in venv. Check logs above for details."
    fi
}


cleanup() {
    echo "🧹 Cleaning up build artifacts..."
    rm -rf build
    deactivate  
    rm -rf "$BUILD_VENV"
}

# --- Main Execution Flow ---
build() {
    check_environment
    setup_venv
    install_dependencies
    create_wrapper 
}

build
