@echo off
rem Starts the demo, then RemoteVI Server shares its window on port 8101 for the whole network.
echo The demo will be reachable from other computers on port 8101 (plain HTTP).
echo Everyone who has the link can operate it. Use this only on a trusted network.
choice /m "Share it with the network"
if errorlevel 2 exit /b 0
call "%~dp0_start demo.cmd"
start "" "%~dp0RemoteVI Server\RemoteVI Server.exe" -- --share "RemoteVI Demo.vi" --port 8101 --whole-network
