@echo off
setlocal
set ROOT=%~dp0..
set FRONTEND_DIST=%ROOT%\frontend-dist

if exist "%FRONTEND_DIST%\index.html" (
  echo [frontend] built dist detected at %FRONTEND_DIST%
  echo [frontend] demo bundle already copies dist into Spring Boot static resources
  echo [frontend] no standalone frontend server is required for the main demo path
  exit /b 0
)

echo [frontend] skipped: missing built dist
echo [frontend] expected:
echo   %FRONTEND_DIST%\index.html
endlocal
