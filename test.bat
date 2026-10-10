@echo off
setlocal
cd /d "%~dp0"
if not exist bin\minicompiler.exe call build.bat
if not exist bin\minicompiler.exe exit /b 1
python tests\verify.py %*
endlocal
