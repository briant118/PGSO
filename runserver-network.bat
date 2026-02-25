@echo off
cd /d "%~dp0"
echo.
echo ============================================
echo   PGSO - Start server for OTHER PCs
echo ============================================
echo.
echo Other PCs must use:  http://YOUR_IP:8000
echo Get your IP: run  ipconfig   and look for IPv4 (e.g. 192.168.1.32)
echo.
echo KEEP THIS WINDOW OPEN. Closing it stops the server.
echo.
python manage.py runserver 0.0.0.0:8000
pause
