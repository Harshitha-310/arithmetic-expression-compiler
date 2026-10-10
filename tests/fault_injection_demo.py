#!/usr/bin/env python3
"""Safely demonstrate that the verification harness detects a known bug.

Creates a temporary copy, mutates multiplication into addition, compiles that
faulty copy, and runs the normal verifier against it. The working source and
normal build are never modified. The temporary directory is removed on exit.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "minicompiler.cpp"
VERIFY = ROOT / "tests" / "verify.py"


def main() -> int:
    compiler = shutil.which("g++") or shutil.which("clang++") or shutil.which("c++")
    if not compiler:
        print("ERROR: No C++ compiler found on PATH. Install GCC/MinGW-w64 first.", file=sys.stderr)
        return 2

    original = SOURCE.read_text(encoding="utf-8")
    correct_line = "case '*': return checkedMul(a, b);"
    faulty_line = "case '*': return checkedAdd(a, b); // INTENTIONAL DEMO BUG"
    if original.count(correct_line) != 1:
        print("ERROR: Could not find the expected multiplication implementation; no files changed.", file=sys.stderr)
        return 2

    print("[1/4] Creating an isolated temporary copy...")
    with tempfile.TemporaryDirectory(prefix="minicompiler_fault_demo_") as temp:
        temp_root = Path(temp)
        (temp_root / "src").mkdir()
        (temp_root / "tests").mkdir()
        (temp_root / "reports").mkdir()
        mutated = original.replace(correct_line, faulty_line, 1)
        (temp_root / "src" / "minicompiler.cpp").write_text(mutated, encoding="utf-8")
        shutil.copy2(VERIFY, temp_root / "tests" / "verify.py")
        faulty_exe = temp_root / ("minicompiler_faulty.exe" if os.name == "nt" else "minicompiler_faulty")

        print("[2/4] Compiling the temporary version with a deliberate multiplication bug...")
        build = subprocess.run(
            [compiler, "-std=c++17", "-O0", str(temp_root / "src" / "minicompiler.cpp"), "-o", str(faulty_exe)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )
        if build.returncode != 0:
            print(build.stdout)
            print(build.stderr, file=sys.stderr)
            print("ERROR: Temporary faulty build failed; the working project remains untouched.", file=sys.stderr)
            return 2

        print("[3/4] Running the normal verification harness against the faulty executable...")
        check = subprocess.run(
            [sys.executable, str(temp_root / "tests" / "verify.py"), "--exe", str(faulty_exe),
             "--cases", "10", "--seed", "20261009", "--no-differential"],
            cwd=temp_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
        )
        print(check.stdout)
        report = temp_root / "reports" / "failures.jsonl"
        report_has_failure = report.is_file() and report.stat().st_size > 0
        if check.returncode == 0 or not report_has_failure:
            print("ERROR: The verifier did not detect the injected bug as expected.", file=sys.stderr)
            return 1

        print("[4/4] SUCCESS: The verifier detected the deliberate bug and wrote a failure report.")
        print("The temporary faulty source, executable, and report will now be deleted automatically.")
        print("Your normal src/minicompiler.cpp and bin/minicompiler.exe were not modified.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
