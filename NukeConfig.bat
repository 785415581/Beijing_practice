@ECHO off
SET Nuke_ROOT=D:\Han_Software_Install\Nuke10.0v3
SET PATH=%PATH%;%Nuke_ROOT%

reg add "HKEY_CURRENT_USER\Software\Microsoft\Command Processor" /v "DisableUNCCheck" /t "REG_DWORD" /d "1" /f

SET TOOLS_PATH=G:\Beijing
SET NUKE_PATH=%TOOLS_PATH%;

ECHO [OF] Info: Launch %Nuke_ROOT%\Nuke10.0.exe %*
Nuke10.0.exe %*