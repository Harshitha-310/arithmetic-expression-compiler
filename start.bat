@echo off
setlocal
cd /d "%~dp0"
title Arithmetic Expression Compiler & Verification Framework

:menu
cls
echo ============================================================
echo   ARITHMETIC EXPRESSION COMPILER ^& VERIFICATION FRAMEWORK
echo ============================================================
echo.
echo   1. Build / check the C++ program
echo   2. Try an arithmetic expression
echo   3. Run the standard verification tests
echo   4. Run a larger randomized + GCC comparison test
echo   5. Demonstrate that the tests can catch a deliberate bug
echo   6. Open the project guide (README)
echo   7. Exit
echo.
choice /c 1234567 /n /m "Choose an option (1-7): "
if errorlevel 7 goto end
if errorlevel 6 goto readme
if errorlevel 5 goto faultdemo
if errorlevel 4 goto stresstest
if errorlevel 3 goto standardtest
if errorlevel 2 goto expression
if errorlevel 1 goto build

goto menu

:build
cls
echo [BUILD] Checking and compiling the project...
call build.bat
echo.
pause
goto menu

:expression
cls
if not exist bin\minicompiler.exe (
  echo The executable was not found. Building it first...
  call build.bat
  if errorlevel 1 (
    echo.
    echo Build failed. Check that g++ is installed and on PATH.
    pause
    goto menu
  )
)
echo Enter an integer arithmetic expression.
echo Example: (2 + 3) * 4
set "EXPR="
set /p "EXPR=Expression: "
if not defined EXPR (
  echo No expression entered.
  pause
  goto menu
)
echo.
bin\minicompiler.exe --all "%EXPR%"
echo.
pause
goto menu

:standardtest
cls
echo [TEST] Running the standard verification suite...
call test.bat
echo.
pause
goto menu

:stresstest
cls
echo This runs randomized checks and compares with GCC/Clang if available.
echo.
set "CASES=500"
set /p "CASES=Number of random cases [500]: "
if not defined CASES set "CASES=500"
set "SEED=20261009"
set /p "SEED=Random seed [20261009]: "
if not defined SEED set "SEED=20261009"
echo.
call test.bat --cases %CASES% --seed %SEED%
echo.
pause
goto menu

:faultdemo
cls
echo This creates a temporary faulty copy to prove the verifier can detect a bug.
echo Your normal source code and executable are not modified.
echo.
choice /c YN /n /m "Run the fault-detection demonstration? (Y/N): "
if errorlevel 2 goto menu
call demo_fault_detection.bat
echo.
pause
goto menu

:readme
if exist README.md (
  start "Project README" notepad.exe "%~dp0README.md"
) else (
  echo README.md was not found in the project folder.
  pause
)
goto menu

:end
echo.
echo Thank you for using the project.
endlocal
exit /b 0
