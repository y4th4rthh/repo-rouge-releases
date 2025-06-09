@echo off
setlocal

REM Check if Python is already installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed.
    python --version
    pause
    exit /b
)

echo Python not found. Downloading Python installer...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile 'python_installer.exe' -ErrorAction Stop; exit 0 } catch { exit 1 }}"

if %errorlevel% neq 0 (
    echo Failed to download Python installer
    echo Please install Python manually from https://python.org
    pause
    exit /b 1
)

if not exist "python_installer.exe" (
    echo Python installer not found after download
    echo Please install Python manually from https://python.org
    pause
    exit /b 1
)

echo Installing Python...
python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

REM Wait for installation to complete (longer timeout)
echo Waiting for installation to complete...
timeout /t 30 /nobreak >nul

REM Clean up installer
del python_installer.exe

REM Refresh environment variables
call refreshenv >nul 2>&1

REM Verify installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python installation may have failed
    echo Please restart your command prompt or install Python manually
    pause
    exit /b 1
)

echo Python installation completed successfully!
python --version

:run_script
REM Try to run the target script
if exist "reporouge_launcher.py" (
    echo You can proceed with running python reporouge_cli.py --help...
) else (
    echo You can proceed with running python reporouge_cli.py --help...
    pause
)