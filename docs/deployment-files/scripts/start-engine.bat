@echo off
setlocal
set ROOT=%~dp0..
set JAR=%ROOT%\engine-runtime\reviewpulse-engine.jar
set JAVA_BIN=%ROOT%\engine-runtime\jre\bin\java.exe
set IDEA_JAVA=C:\Users\17337\AppData\Local\Programs\IntelliJ IDEA Ultimate 2025.1.3\jbr\bin\java.exe
set CONFIG=%ROOT%\config\engine\application-demo.yml

if exist "%JAVA_BIN%" (
  if exist "%JAR%" (
    start "reviewpulse-engine" "%JAVA_BIN%" -jar "%JAR%" --spring.config.location="%CONFIG%"
    echo [engine] started with bundled java
    exit /b 0
  )
)

if exist "%IDEA_JAVA%" (
  if exist "%JAR%" (
    start "reviewpulse-engine" "%IDEA_JAVA%" -jar "%JAR%" --spring.config.location="%CONFIG%"
    echo [engine] started with IntelliJ bundled java
    exit /b 0
  )
)

echo [engine] skipped: missing runnable jar or java runtime
echo [engine] checked:
echo   %JAVA_BIN%
echo   %IDEA_JAVA%
echo   %JAR%
endlocal
