@echo off
rem Used by the other batch files: starts RemoteVI Demo.exe unless it runs, and waits for its window.
tasklist /fi "imagename eq RemoteVI Demo.exe" | find /i "RemoteVI Demo.exe" >nul && exit /b 0
start "" "%~dp0RemoteVI Demo\RemoteVI Demo.exe"
timeout /t 5 /nobreak >nul
exit /b 0
