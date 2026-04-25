@echo off
REM setup_scheduler.bat — Register Phase 6 heartbeat and daily reflection with Windows Task Scheduler
REM Run this once as Administrator.

SET PYTHON=python
SET SCRIPTS=D:\second-brain-starter\.claude\scripts

echo [1/2] Creating Heartbeat task (every 30 minutes, 9 AM - 10 PM)...
schtasks /create ^
  /tn "SecondBrain\Heartbeat" ^
  /tr "\"%PYTHON%\" \"%SCRIPTS%\heartbeat.py\"" ^
  /sc minute ^
  /mo 30 ^
  /st 09:00 ^
  /et 22:00 ^
  /k ^
  /f
if %ERRORLEVEL%==0 (
    echo    OK: Heartbeat scheduled.
) else (
    echo    ERROR: Failed to create Heartbeat task. Are you running as Administrator?
)

echo.
echo [2/2] Creating DailyReflect task (daily at 8:00 AM)...
schtasks /create ^
  /tn "SecondBrain\DailyReflect" ^
  /tr "\"%PYTHON%\" \"%SCRIPTS%\memory_reflect.py\"" ^
  /sc daily ^
  /st 08:00 ^
  /f
if %ERRORLEVEL%==0 (
    echo    OK: DailyReflect scheduled.
) else (
    echo    ERROR: Failed to create DailyReflect task. Are you running as Administrator?
)

echo.
echo [3/3] Creating TokenReport task (every 4 hours, midnight start)...
schtasks /create ^
  /tn "SecondBrain\TokenReport" ^
  /tr "\"%PYTHON%\" \"%SCRIPTS%\token_report.py\"" ^
  /sc hourly ^
  /mo 4 ^
  /st 00:00 ^
  /f
if %ERRORLEVEL%==0 (
    echo    OK: TokenReport scheduled.
) else (
    echo    ERROR: Failed to create TokenReport task. Are you running as Administrator?
)

echo.
echo Done. Verify in Task Scheduler under SecondBrain\.
echo.
echo To run immediately for testing:
echo   python "%SCRIPTS%\heartbeat.py"
echo   python "%SCRIPTS%\memory_reflect.py"
echo   python "%SCRIPTS%\token_report.py"
echo.
echo To remove tasks:
echo   schtasks /delete /tn "SecondBrain\Heartbeat" /f
echo   schtasks /delete /tn "SecondBrain\DailyReflect" /f
echo   schtasks /delete /tn "SecondBrain\TokenReport" /f
pause
