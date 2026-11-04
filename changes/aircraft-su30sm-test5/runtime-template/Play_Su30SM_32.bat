@echo off
cd /d "%~dp0"
if not exist "user-su30" mkdir "user-su30"
start "" ysflight32_gl1.exe -userdir "%~dp0user-su30" -configdir "%~dp0config-su30" -script Start_Su30SM.script
