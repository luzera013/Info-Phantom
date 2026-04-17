@echo off
echo Iniciando servidor Info-Phantom...
echo.
echo O site estará disponivel em: http://localhost:8080
echo.
cd /d "%~dp0"
python -m http.server 8080 --directory .
pause
