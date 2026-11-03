@echo off
cd /d "%~dp0"
if /I "%PROCESSOR_ARCHITECTURE%"=="AMD64" goto x64
if defined PROCESSOR_ARCHITEW6432 goto x64
call Play_Su30SM_32.bat
exit /b
:x64
call Play_Su30SM_64.bat
