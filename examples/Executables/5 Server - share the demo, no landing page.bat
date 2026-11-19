@echo off
rem Starts the demo, then RemoteVI Server shares its window on port 8102 and runs no landing page.
call "%~dp0_start demo.cmd"
start "" "%~dp0RemoteVI Server\RemoteVI Server.exe" -- --share "RemoteVI Demo.vi" --port 8102 --landing-port 0
