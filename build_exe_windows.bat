@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo 🚀 Starting build process for UniversalVPNTool...

rem Determine project root (directory where the script is located)
set "PROJECT_ROOT=%~dp0"
rem Remove trailing backslash if needed
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo 📁 Project root detected: %PROJECT_ROOT%
cd /d "%PROJECT_ROOT%"

rem Set virtual environment paths
set "VENV_DIR=%PROJECT_ROOT%\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

rem Create virtual environment if missing
if not exist "%VENV_PYTHON%" (
    echo 🐍 Virtual environment not found. Creating one...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment. Ensure Python is installed and in PATH.
        exit /b 1
    )
)

rem Upgrade pip and install dependencies
echo 📦 Installing/upgrading pip and installing requirements...
"%VENV_PYTHON%" -m pip install --upgrade pip
"%VENV_PYTHON%" -m pip install -r requirements.txt pyinstaller

rem Clean previous build artifacts
echo 🧹 Cleaning up old build artifacts...
rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1
del /q *.spec >nul 2>&1

rem Build executable using PyInstaller
echo 🛠️ Building Windows executable...
"%VENV_DIR%\Scripts\pyinstaller.exe" --onefile --name UniversalVPNTool main.py

echo.
echo ✅ Build complete!
echo 📦 Executable is located at: %PROJECT_ROOT%\dist\UniversalVPNTool.exe
