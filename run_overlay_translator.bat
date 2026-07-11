@echo off
setlocal
title OverlayTranslator

rem Always run from the folder this .bat lives in, no matter where it's launched
cd /d "%~dp0"

rem Make sure Python is available
where python >nul 2>nul
if errorlevel 1 (
    echo [Error] Python was not found on your PATH.
    echo Install Python 3.11 from https://www.python.org/downloads/ and try again.
    echo.
    pause
    exit /b 1
)

rem Ensure dependencies are installed; install them on first run if missing
python -c "import customtkinter, pystray, deep_translator, translators, requests, mss, keyboard, pytesseract, PIL" >nul 2>nul
if errorlevel 1 (
    echo First-time setup: installing dependencies, please wait...
    python -m pip install -r requirements.txt
    echo.
)

echo ============================================================
echo  OverlayTranslator is starting.
echo    - Press ALT+Q, then drag a box over English text
echo    - Press ESC or click the bubble to dismiss it
echo    - Press CTRL+C in this window to quit
echo ============================================================
echo.

python main.py

echo.
echo OverlayTranslator has stopped.
pause
