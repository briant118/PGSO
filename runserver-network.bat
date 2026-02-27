@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo.
echo ============================================
echo   PGSO - Start server for OTHER DEVICES
echo ============================================
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
  set "raw=%%a"
  set "MYIP=!raw:~1!"
)
if defined MYIP (
  echo   EXPO APP: Double-click start-expo.bat (or: cd pgso-app ^& npx expo start)
  echo   Then scan the Expo QR with Expo Go app on your phone.
  echo.
  echo   Set API_BASE_URL in pgso-app/config.js to: http://!MYIP!:8000
  echo   CRITICAL: Include  http://  and  :8000
  echo.
) else (
  echo   Run "ipconfig" to get your IPv4, then use: http://YOUR_IP:8000
  echo.
)

echo   If "connection refused": Run allow-port-8000-firewall.ps1 as Administrator
echo.
echo   KEEP THIS WINDOW OPEN.
echo.
python manage.py runserver 0.0.0.0:8000
pause
