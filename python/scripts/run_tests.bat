@echo off
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%~dp0..\tools\run_tests.py" %*
) else (
    python "%~dp0..\tools\run_tests.py" %*
)
set rc=%errorlevel%
pause
exit /b %rc%
