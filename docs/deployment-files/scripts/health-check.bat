@echo off
setlocal
echo [health] checking Spring Boot on http://127.0.0.1:8080
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8080' -UseBasicParsing -TimeoutSec 3; Write-Host '[health] engine reachable' } catch { Write-Host '[health] engine not ready' }"
echo [health] checking Agent on http://127.0.0.1:8001/
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8001/' -UseBasicParsing -TimeoutSec 3; Write-Host '[health] agent reachable' } catch { Write-Host '[health] agent not ready' }"
endlocal

