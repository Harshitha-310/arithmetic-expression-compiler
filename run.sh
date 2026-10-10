#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
[ -x bin/minicompiler ] || ./build.sh
exec ./bin/minicompiler "$@"
