@echo off
setlocal

if "%~1"=="" (
    echo ================================================
    echo  Drag a WhatsApp video onto this script to
    echo  process it for the signage display.
    echo ================================================
    pause
    exit /b 1
)

set "INPUT=%~1"
set "FILENAME=%~nx1"
set "OUTPUT=%~dp0media\%FILENAME%"
set "TMPOUT=%TEMP%\signage_tmp_%RANDOM%.mp4"

echo.
echo  Input:  %INPUT%
echo  Output: %OUTPUT%
echo.

ffmpeg -y -i "%INPUT%" -vf "transpose=1" -c:v libx264 -crf 18 -preset fast -c:a aac -movflags +faststart "%TMPOUT%"

echo.
if %errorlevel%==0 (
    move /y "%TMPOUT%" "%OUTPUT%" >nul
    echo  [OK] Saved to media\%FILENAME%
    echo  Add it to SLIDES in index.html and you are done.
) else (
    del /f /q "%TMPOUT%" 2>nul
    echo  [ERROR] Processing failed. Check the output above.
)

echo.
pause
