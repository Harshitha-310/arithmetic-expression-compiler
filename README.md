# Arithmetic Expression Compiler & Verification Framework 

A small arithmetic-expression compiler and verification harness built with **C++17 and Python 3**. It has no Java, ANTLR, Python package, or third-party C++ library dependency.

> This is an educational mini compiler for arithmetic expressions, not a production compiler or a full C/C++ compiler. Differential testing checks a restricted, generated set of well-defined integer expressions against a local GCC/Clang C++ compiler.

## Features

**Version 1.1 addition:** the `%` modulo operator is supported, including precedence, AST evaluation, IR emission, zero-divisor handling, randomized cases, and differential tests.

- Token display for integer literals, operators and parentheses.
- Recursive-descent parser with precedence and left associativity. Multiplication, division, and modulo share precedence.
- AST-based evaluation for `+`, `-`, `*`, `/`, `%` (modulo), unary `+`/`-`, and parentheses.
- Portable C++17 integer overflow checks and division/modulo-by-zero detection.
- Three-address intermediate representation (IR).
- Constant-folding optimization for safe constant expressions.
- Deterministic unit tests for normal and malformed expressions.
- Randomized expression generation with a reproducible seed.
- Optional differential testing against `g++`, `clang++`, or `c++`.
- JSON Lines failure report containing exact expressions and errors.
- **Version 1.2 addition:** safe fault-injection demonstration that introduces a known bug only in a temporary copy, then confirms the verifier catches it; the real source and executable are never changed.

## Requirements

### Windows

1. Install MSYS2 from https://www.msys2.org/.
2. Open **MSYS2 UCRT64** and install GCC:

   ```bash
   pacman -S --needed mingw-w64-ucrt-x86_64-gcc
   ```

3. Add `C:\msys64\ucrt64\bin` to Windows `Path` (Environment Variables).
4. Install Python 3 from https://www.python.org/downloads/windows/ and enable **Add Python to PATH**.
5. Open a new Command Prompt and verify `g++ --version` and `python --version`.

### Linux

Install `g++` and Python 3 with your distribution's package manager.

## Easiest way to use it on Windows

After installing GCC and Python once, double-click `start.bat` or open CMD in this folder and run:

```bat
start.bat
```

The menu lets you build the program, try an expression, run the standard tests, run a larger randomized/differential test, demonstrate safe fault detection, or open this guide. You can still use `build.bat`, `run.bat`, `test.bat`, and `demo_fault_detection.bat` directly.

## Build on Windows (CMD)

Open the extracted project folder in File Explorer, click the address bar, type `cmd`, and press Enter. Then run:

```bat
build.bat
```

This creates `bin\minicompiler.exe`.

## Build on Linux/macOS with g++ available

```bash
chmod +x build.sh run.sh test.sh
./build.sh
```

## Run examples

Windows CMD:

```bat
run.bat --help
run.bat --all "3 + 4 * 5"
run.bat --ir "(2 + 3) * 4"
run.bat --optimize "(10 - 2) * (3 + 1)"
run.bat --result "20 / 5 / 2"
run.bat --all "17 % 5 * 3 + 1"
```

Linux:

```bash
./run.sh --all "3 + 4 * 5"
./run.sh --result "20 / 5 / 2"
```

Expected key results include `23`, `20`, `32`, and `2` respectively. The `%` operator computes the integer remainder, for example `run.bat --result "17 % 5"` returns `2`.

Options:

- `--result`: print only the computed integer (used by test automation).
- `--tokens`: display lexer tokens.
- `--ir`: display three-address intermediate representation.
- `--optimize`: run constant folding before evaluation.
- `--all`: display tokens, optimization note, IR and final result.
- `--help`, `--version`: show command help or version.

## Run tests

Windows:

```bat
test.bat
```

Linux:

```bash
./test.sh
```

The default suite runs fixed tests, 100 randomized expressions (seed `20261009`) and, if a C++ reference compiler is available, compares the mini compiler's results with a compiled C++ program. It builds the reference program once for the whole batch.

Customize the randomized test run:

```bat
test.bat --cases 500 --seed 42
```

### Demonstrate failure detection safely

To prove that the test harness can catch a defect, run this in Windows CMD:

```bat
demo_fault_detection.bat
```

The demo makes a temporary copy of the source, deliberately changes multiplication to addition, compiles that faulty copy, and runs the regular tests against it. It succeeds only if the tests detect the injected bug and write a failure report. All demo files live in a temporary directory and are automatically deleted; your normal source and `bin\minicompiler.exe` are not modified. Requires Python 3 and a C++ compiler on `PATH`.


Use a specific reference compiler:

```bat
test.bat --cases 250 --compiler clang++
```

Skip differential comparison (unit + randomized checks still run):

```bat
test.bat --no-differential
```

### Failure reporting

The harness resets and writes `reports/failures.jsonl` each run. If a case fails, its expression, expected/actual detail, test kind and seed are recorded. To reproduce a random failure, rerun using the same seed and inspect the listed expression.

Differential testing is only meaningful for well-defined, bounded integer expressions. The generator avoids division by zero and keeps intermediate values small to avoid overflow. It does not prove compiler correctness or automatically identify which compiler is defective.

## Project structure

```text
MiniCompiler_Verification/
├── src/minicompiler.cpp       # C++17 lexer-style token display, parser, AST, evaluator, optimizer, IR
├── tests/verify.py            # unit, randomized and differential test harness
├── tests/fault_injection_demo.py # isolated deliberate-bug detection demonstration
├── examples/                  # sample inputs/commands
├── reports/                   # generated failure report location
├── start.bat                   # interactive Windows menu for common actions
├── build.bat / build.sh        # compile source
├── run.bat / run.sh            # run the compiler
├── test.bat / test.sh          # run verification suite
├── demo_fault_detection.bat    # safe fault-injection demonstration
├── README.md
└── .gitignore
```

## Limitations and next improvements

- The language currently supports integer arithmetic (`+`, `-`, `*`, `/`, `%`) only; it does not implement variables, functions, types, or machine-code generation.
- The emitted three-address IR is educational text, not executable LLVM IR.
- Constant folding is intentionally conservative around arithmetic errors.
- Random differential tests are not a formal proof and may miss defects.
- Useful future improvements: property-based AST generation, test-case shrinking, more systematic overflow tests, sanitizer runs, and a compiler-specific test corpus.


- Implemented a C++17 recursive-descent parser and AST evaluator for arithmetic expressions, with operator precedence, unary operators, overflow checks, and division-by-zero handling.
- Generated three-address intermediate representation and implemented conservative constant folding.
- Added modulo support and checked arithmetic edge cases, including overflow and division/modulo by zero.
- Built a Python verification harness with deterministic regression tests, seeded randomized expression generation, optional GCC/Clang differential comparison, and JSONL failure reports.
