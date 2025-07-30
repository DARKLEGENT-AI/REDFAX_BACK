@echo off
title LocalTunnel Auto-Restart Forever (no sleep)

:loop
echo.
echo [LT] Starting tunnel at %TIME%
lt --port 8000 --subdomain redfax-server

echo [LT] Tunnel exited or crashed at %TIME%. Restarting immediately...
goto loop