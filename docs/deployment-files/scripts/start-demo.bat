@echo off
setlocal

set ROOT=%~dp0..
echo [demo] root=%ROOT%
echo [demo] make sure review_pulse_demo has been imported and API_KEY is filled

call "%~dp0start-agent.bat"
echo [demo] waiting for agent on http://127.0.0.1:8001/
powershell -NoProfile -Command ^
  "$deadline=(Get-Date).AddSeconds(60);" ^
  "while((Get-Date) -lt $deadline) {" ^
  "  try { Invoke-WebRequest -Uri 'http://127.0.0.1:8001/' -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host '[demo] agent ready'; exit 0 }" ^
  "  catch { Start-Sleep -Seconds 2 }" ^
  "}" ^
  "Write-Host '[demo] agent wait timed out'; exit 1"

call "%~dp0start-engine.bat"
echo [demo] waiting for engine on http://127.0.0.1:8080
powershell -NoProfile -Command ^
  "$deadline=(Get-Date).AddSeconds(60);" ^
  "while((Get-Date) -lt $deadline) {" ^
  "  try { Invoke-WebRequest -Uri 'http://127.0.0.1:8080' -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host '[demo] engine ready'; exit 0 }" ^
  "  catch { Start-Sleep -Seconds 2 }" ^
  "}" ^
  "Write-Host '[demo] engine wait timed out'; exit 1"

call "%~dp0start-frontend.bat"

echo [demo] startup sequence finished
echo [demo] open http://127.0.0.1:8080
endlocal
