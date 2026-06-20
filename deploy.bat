@echo off
set SCRIPT_DIR=%~dp0
copy /y "%SCRIPT_DIR%deploy.txt" "%TEMP%\vpstr_deploy.bat" >nul
call "%TEMP%\vpstr_deploy.bat"
del "%TEMP%\vpstr_deploy.bat" >nul 2>&1
pause
