#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
command -v g++ >/dev/null 2>&1 || { echo "ERROR: g++ is required (C++17)." >&2; exit 1; }
mkdir -p bin
echo "[BUILD] Compiling MiniCompiler with C++17..."
g++ -std=c++17 -O2 -Wall -Wextra -pedantic src/minicompiler.cpp -o bin/minicompiler
echo "[BUILD OK] bin/minicompiler"
./bin/minicompiler --version
