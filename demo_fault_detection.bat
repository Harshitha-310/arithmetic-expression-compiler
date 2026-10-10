@echo off
setlocal
cd /d "%~dp0"
python tests\fault_injection_demo.py
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo Fault-injection demonstration completed successfully.
) else (
  echo Fault-injection demonstration did not complete. Review the message above.
)
endlocal & exit /b %RESULT%
