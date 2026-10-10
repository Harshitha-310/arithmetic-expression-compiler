#!/usr/bin/env python3
"""Unit, randomized and differential tests for MiniCompiler.

Usage: python tests/verify.py [--cases 100] [--seed 2026] [--no-differential]
A failing randomized case is written to reports/failures.jsonl for reproduction.
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXE = ROOT / "bin" / ("minicompiler.exe" if os.name == "nt" else "minicompiler")
FAILURES = ROOT / "reports" / "failures.jsonl"


def run_compiler(exe: Path, expression: str):
    p = subprocess.run([str(exe), "--result", expression], text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"exit code {p.returncode}")
    try:
        return int(p.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"unexpected output: {p.stdout!r}") from exc


def make_expression(rng, depth=0):
    """Return a bounded, well-defined C++ arithmetic expression and its value."""
    if depth >= 3 or rng.random() < 0.28:
        value = rng.randint(0, 12)
        if rng.random() < 0.18:
            return f"(-{value})", -value
        return str(value), value
    for _ in range(100):
        left, a = make_expression(rng, depth + 1)
        right, b = make_expression(rng, depth + 1)
        op = rng.choice(["+", "-", "*", "/", "%"])
        if op in ("/", "%"):
            if b == 0:
                continue
            if op == "/":
                value = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)  # truncate toward zero
            else:
                quotient = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)
                value = a - quotient * b  # C++ remainder sign follows the dividend
        elif op == "+": value = a + b
        elif op == "-": value = a - b
        else: value = a * b
        if abs(value) <= 100000 and abs(a) <= 100000 and abs(b) <= 100000:
            return f"({left} {op} {right})", value
    return "(7 + 2)", 9


def discover_reference_compiler(requested=None):
    if requested:
        path = shutil.which(requested)
        if path:
            return path
        raise RuntimeError(f"Requested reference compiler not found on PATH: {requested}")
    for name in ("g++", "clang++", "c++"):
        path = shutil.which(name)
        if path:
            return path
    return None


def record_failure(item):
    FAILURES.parent.mkdir(parents=True, exist_ok=True)
    with FAILURES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Run unit and differential compiler tests")
    ap.add_argument("--exe", default=str(DEFAULT_EXE), help="path to minicompiler executable")
    ap.add_argument("--cases", type=int, default=100, help="number of randomized expressions")
    ap.add_argument("--seed", type=int, default=20261009, help="random seed for reproducibility")
    ap.add_argument("--compiler", help="reference compiler executable (g++ or clang++)")
    ap.add_argument("--no-differential", action="store_true", help="skip GCC/Clang comparison")
    args = ap.parse_args()
    exe = Path(args.exe).resolve()
    if not exe.is_file():
        print(f"ERROR: executable not found: {exe}\nRun build.bat or ./build.sh first.", file=sys.stderr)
        return 2
    FAILURES.parent.mkdir(parents=True, exist_ok=True)
    FAILURES.write_text("", encoding="utf-8")
    passed = failed = 0

    def check(name, action, expected=None):
        nonlocal passed, failed
        try:
            actual = action()
            if expected is not None and actual != expected:
                raise AssertionError(f"expected {expected}, got {actual}")
            passed += 1
            print(f"[PASS] {name}")
            return actual
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name}: {e}")
            record_failure({"kind": "unit", "name": name, "error": str(e)})
            return None

    fixed = [
        ("precedence", "3 + 4 * 5", 23),
        ("parentheses", "(2 + 3) * 4", 20),
        ("left associativity", "20 / 5 / 2", 2),
        ("subtraction", "10 - 3 - 2", 5),
        ("unary minus", "-5 + 8", 3),
        ("unary plus", "+7 * 2", 14),
        ("nested parentheses", "((2+3)*(4-1))", 15),
        ("modulo", "17 % 5", 2),
        ("modulo precedence", "17 % 5 * 3 + 1", 7),
        ("negative modulo", "-17 % 5", -2),
        ("whitespace", "  12   /  3 ", 4),
        ("constant folding", "3 + 4 * 5", 23),
    ]
    for name, expr, expected in fixed:
        check(name, lambda e=expr: run_compiler(exe, e), expected)

    def check_optimization_output():
        p = subprocess.run([str(exe), "--all", "3 + 4 * 5"], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        if p.returncode != 0:
            raise RuntimeError(p.stderr.strip() or f"exit code {p.returncode}")
        if "OPTIMIZATION:" not in p.stdout or "THREE-ADDRESS IR:" not in p.stdout or "RESULT: 23" not in p.stdout:
            raise AssertionError("--all output is missing optimization, IR, or expected result")
        return True
    check("optimization and IR output", check_optimization_output, True)

    for name, expr in [("division by zero", "8 / 0"), ("missing operand", "4 +"),
                       ("missing close paren", "(3 + 2"), ("unexpected character", "2 @ 3"),
                       ("modulo by zero", "9 % 0"),
                       ("addition overflow", "9223372036854775807 + 1"),
                       ("multiplication overflow", "3037000500 * 3037000500"),
                       ("integer literal overflow", "9223372036854775808")]:
        def should_fail(e=expr):
            p = subprocess.run([str(exe), "--result", e], text=True, capture_output=True, timeout=3)
            if p.returncode == 0:
                raise AssertionError("invalid expression unexpectedly succeeded")
            return "rejected"
        check(name, should_fail, "rejected")

    rng = random.Random(args.seed)
    cases = [make_expression(rng) for _ in range(max(0, args.cases))]
    for idx, (expr, expected) in enumerate(cases, 1):
        try:
            actual = run_compiler(exe, expr)
            if actual != expected:
                raise AssertionError(f"expected {expected}, got {actual}")
            passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] random case {idx}: {expr}: {e}")
            record_failure({"kind": "random", "seed": args.seed, "case": idx,
                            "expression": expr, "expected": expected, "error": str(e)})
    print(f"[INFO] Randomized expression checks: {len(cases)} cases (seed={args.seed})")

    ref = None if args.no_differential else discover_reference_compiler(args.compiler)
    if not args.no_differential and ref is None:
        print("[WARN] No g++/clang++ found; differential comparison skipped. Install a C++ compiler to enable it.")
    if ref and cases:
        try:
            with tempfile.TemporaryDirectory(prefix="minicompiler_diff_") as td:
                td = Path(td)
                source = td / "reference.cpp"
                binary = td / ("reference.exe" if os.name == "nt" else "reference")
                lines = ["#include <iostream>", "int main() {", "  std::cout << std::unitbuf;" ]
                for expr, _ in cases:
                    lines.append(f'  std::cout << (long long)({expr}) << "\\n";')
                lines.append("  return 0;\n}")
                source.write_text("\n".join(lines), encoding="utf-8")
                build = subprocess.run([ref, "-std=c++17", str(source), "-o", str(binary)],
                                       text=True, capture_output=True, timeout=30)
                if build.returncode != 0:
                    raise RuntimeError("reference compiler failed: " + build.stderr[-1500:])
                output = subprocess.run([str(binary)], text=True, capture_output=True, timeout=10)
                if output.returncode != 0:
                    raise RuntimeError("reference executable failed: " + output.stderr)
                ref_values = [int(x) for x in output.stdout.splitlines()]
                if len(ref_values) != len(cases):
                    raise RuntimeError("reference compiler returned an unexpected number of results")
                for idx, ((expr, _), expected_ref) in enumerate(zip(cases, ref_values), 1):
                    try:
                        actual = run_compiler(exe, expr)
                        if actual != expected_ref:
                            raise AssertionError(f"MiniCompiler={actual}; {Path(ref).name}={expected_ref}")
                        passed += 1
                    except Exception as e:
                        failed += 1
                        print(f"[FAIL] differential case {idx}: {expr}: {e}")
                        record_failure({"kind": "differential", "compiler": ref, "seed": args.seed,
                                        "case": idx, "expression": expr, "error": str(e)})
                print(f"[INFO] Differential comparison against {Path(ref).name}: {len(cases)} expressions")
        except Exception as e:
            failed += 1
            print(f"[FAIL] differential harness: {e}")
            record_failure({"kind": "harness", "error": str(e)})

    print("\n================ VERIFICATION SUMMARY ================")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Random seed: {args.seed}")
    print(f"Failure report: {FAILURES.relative_to(ROOT)}")
    if failed:
        print("Reproduce random cases with the same --seed; inspect the JSONL report for exact expressions.")
        return 1
    print("All enabled checks passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
