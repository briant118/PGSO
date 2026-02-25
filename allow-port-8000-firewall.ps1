# Run this script as Administrator (right-click PowerShell -> Run as administrator)
# It allows incoming TCP connections on port 8000 so other PCs can access the app.

$ruleName = "Django PGSO - Port 8000"
# Remove old rule if it exists
netsh advfirewall firewall delete rule name="$ruleName" 2>$null
# Add new rule
netsh advfirewall firewall add rule name="$ruleName" dir=in action=allow protocol=TCP localport=8000
Write-Host "Done. Port 8000 is now allowed. Start the server with runserver-network.bat" -ForegroundColor Green
