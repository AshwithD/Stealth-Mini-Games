@echo off
chcp 65001 >nul
title StealthGame .exe builder

REM ============================================================
REM  StealthGame .exe builder for Windows 11
REM  pygame 2.6.x ships prebuilt binaries only up to Python 3.13,
REM  so this script auto-selects Python 3.12 / 3.13 if available.
REM  Written without if-blocks so it works from any folder path.
REM ============================================================

REM ---------- Step 1: pick a suitable Python interpreter ----------
set "PYCMD="
py -3.12 --version >nul 2>nul && set "PYCMD=py -3.12"
if not defined PYCMD py -3.13 --version >nul 2>nul && set "PYCMD=py -3.13"
if not defined PYCMD py --version >nul 2>nul && set "PYCMD=py"
if not defined PYCMD python --version >nul 2>nul && set "PYCMD=python"

if defined PYCMD goto :havepython
echo ERROR: Python not found.
echo Install Python 3.12 from https://www.python.org/downloads/
echo During setup, check "Add python.exe to PATH".
pause
exit /b 1

:havepython
echo Using: %PYCMD%
%PYCMD% --version

REM ---------- Step 2: Python must be 3.10 - 3.13 for pygame wheels ----------
%PYCMD% --version | findstr /r /c:"^Python 3\.1[0-3]" >nul
if errorlevel 1 goto :pytoonew

REM ---------- Step 3: install dependencies ----------
%PYCMD% -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :pipfail
%PYCMD% -m pip install pygame pyinstaller
if errorlevel 1 goto :pipfail2

REM ---------- Step 4: build the .exe ----------
%PYCMD% -m PyInstaller --noconfirm --onefile --windowed --name StealthGame stealth_game.py
if errorlevel 1 goto :buildfail

echo.
echo Build succeeded! Output: %CD%\dist\StealthGame.exe
pause
exit /b 0

:pytoonew
echo.
echo ERROR: pygame 2.6.1 has NO prebuilt binaries for Python 3.14+.
echo Your Python version is too new, so pip tries to compile pygame from source.
echo.
echo Fix: install Python 3.12 from https://www.python.org/downloads/
echo Then run this file again.
pause
exit /b 1

:pipfail
echo ERROR: pip upgrade failed - check your internet connection.
pause
exit /b 1

:pipfail2
echo ERROR: failed to install pygame/pyinstaller - see messages above.
pause
exit /b 1

:buildfail
echo ERROR: build failed - see messages above.
pause
exit /b 1
