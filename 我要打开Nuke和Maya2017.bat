@ECHO OFF

COLOR A

title MyWindow
echo The CATALINA_HOME environment variable is not defined correctly
echo=
echo This environment variable is needed to run this program

set "CATALINA_HOME=%cd%"

echo This is current path "%CATALINA_HOME%"
rem 这只是注释
echo I want to start it

start D:\Nuke10.0v3\Nuke10.0.exe
start D:\Maya2017\bin\maya.exe

pause



rem cls清除当前界面的所有信息
