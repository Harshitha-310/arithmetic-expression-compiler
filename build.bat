@echo off
setlocal
cd /d "%~dp0"
where g++ >nul 2>nul
if errorlevel 1 (
  echo ERROR: g++ was not found on PATH.
  echo Install MSYS2 MinGW-w64 GCC and add C:\msys64\ucrt64\bin to PATH.
  exit /b 1
)
if not exist bin mkdir bin
echo [BUILD] Compiling MiniCompiler with C++17...
g++ -std=c++17 -O2 -Wall -Wextra -pedantic src\minicompiler.cpp -o bin\minicompiler.exe
if errorlevel 1 (
  echo [BUILD FAILED] Review the compiler errors above.
  exit /b 1
)
echo [BUILD OK] bin\minicompiler.exe
bin\minicompiler.exe --version
endlocal
