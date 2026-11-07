@echo off
rem Starts the demo, then RemoteVI Server shares its window on port 8100: the browser only watches.
call "%~dp0_start demo.cmd"
start "" "%~dp0RemoteVI Server\RemoteVI Server.exe" -- --share "RemoteVI Demo.vi" --port 8100 --view-only
