@echo off
if "%~1"=="" (
    echo Drag and drop a video file onto this bat file.
    pause
    exit
)
set SCRIPT_DIR=%~dp0
set INPUT=%~1
set OUTPUT=%~dp0media\%~n1.mp4
set TMPOUT=%~dp0media\_tmp_%~n1.mp4
copy /y "%SCRIPT_DIR%process_video.txt" "%TEMP%\vpstr_process.bat" >nul
call "%TEMP%\vpstr_process.bat"
del "%TEMP%\vpstr_process.bat" >nul 2>&1
pause
