@echo off
setlocal
cd /d "%~dp0"
if not exist "ysflight32_gl1.exe" (
 echo Put START_SAFE.cmd next to ysflight32_gl1.exe in the extracted game folder.
 pause
 exit /b 1
)
if not exist "startup_safe_config" mkdir "startup_safe_config"
if not exist "startup_safe_config" (
 echo Cannot create startup_safe_config. Move the extracted game to a writable folder.
 pause
 exit /b 1
)
>"startup_safe_config\option.cfg" echo SCREENMOD 0
>>"startup_safe_config\option.cfg" echo RMBRWSIZE FALSE
>>"startup_safe_config\option.cfg" echo SOUND FALSE
>>"startup_safe_config\option.cfg" echo OPENDEMO FALSE
>>"startup_safe_config\option.cfg" echo FONTHEIGHT 16
>>"startup_safe_config\option.cfg" echo LANGUAGE FILE:ru.uitxt
 echo Starting YSFlight with separate temporary settings. Keep this window open.
 echo Diagnostic log: startup_log.txt
"ysflight32_gl1.exe" -configdir startup_safe_config >"startup_log.txt" 2>&1
set "ys_exit=%errorlevel%"
echo Exit code: %ys_exit%
echo Exit code: %ys_exit%>>"startup_log.txt"
pause
