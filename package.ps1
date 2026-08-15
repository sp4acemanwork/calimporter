# --- Configuration ---
$APP_NAME = "configurator"
$ENTRY_POINT = "main.py"
$OUTPUT_DIR = "dist"
$BUILD_VENV = "venv"
$REQ_FILE = "requirementswin.txt"

# --- Helper Functions ---
function Check-Environment {
    Write-Host "[INFO] Checking environment..."
    
    # Check for 'python' or 'py' launcher on Windows
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        $script:PythonCmd = "python"
    } elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
        $script:PythonCmd = "py"
    } else {
        Write-Error "[ERROR] Python could not be found in PATH. Please install Python to continue."
        exit 1
    }
    
    Write-Host "[OK] Environment check passed (Using '$script:PythonCmd')."
}

function Setup-Venv {
    Write-Host "[INFO] Creating temporary build virtual environment..."
    if (Test-Path $BUILD_VENV) { 
        Remove-Item -Recurse -Force $BUILD_VENV 
    }
    
    & $script:PythonCmd -m venv $BUILD_VENV
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "[ERROR] Failed to create virtual environment."
        exit 1
    }
}

function Install-Dependencies {
    Write-Host "[INFO] Installing dependencies..."
    $venvPython = Join-Path $BUILD_VENV "Scripts\python.exe"
    
    # Upgrade pip
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Write-Error "[ERROR] Pip upgrade failed."; exit 1 }

    # Explicitly install pyinstaller along with requirementswin.txt
    if (Test-Path $REQ_FILE) {
        & $venvPython -m pip install pyinstaller -r $REQ_FILE
    } else {
        Write-Warning "[WARN] '$REQ_FILE' not found. Installing pyinstaller only..."
        & $venvPython -m pip install pyinstaller
    }

    if ($LASTEXITCODE -ne 0) { 
        Write-Error "[ERROR] Failed to install dependencies."
        exit 1 
    }
}

function Compile-App {
    Write-Host "[INFO] Compiling $APP_NAME to .exe..."
    $venvPyInstaller = Join-Path $BUILD_VENV "Scripts\pyinstaller.exe"
    
    if (-not (Test-Path $venvPyInstaller)) {
        Write-Error "[ERROR] pyinstaller.exe not found in virtual environment."
        exit 1
    }
    
    & $venvPyInstaller --noconfirm --onefile --clean `
        --name $APP_NAME `
        --distpath $OUTPUT_DIR `
        --collect-all textual `
        --collect-all rich `
        $ENTRY_POINT
        
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "[ERROR] PyInstaller compilation failed."
        exit 1 
    }
    Write-Host "[OK] Compilation complete: $OUTPUT_DIR\$APP_NAME.exe"
}

function Cleanup-Build {
    Write-Host "[INFO] Cleaning up temporary build artifacts..."
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "$APP_NAME.spec") { Remove-Item -Force "$APP_NAME.spec" }
    if (Test-Path $BUILD_VENV) { Remove-Item -Recurse -Force $BUILD_VENV }
    Write-Host "[OK] Clean up finished."
}

# --- Main Execution Flow ---
function Invoke-Build {
    Check-Environment
    Setup-Venv
    Install-Dependencies
    Compile-App
    Cleanup-Build
}

Invoke-Build
