@echo off
echo Iniciando StarCompanion...
cd /d "%~dp0"

if exist "bin\StarCompanion.exe" (
    start /b "" "bin\StarCompanion.exe"
) else (
    if exist "dist\StarCompanion.exe" (
        start /b "" "dist\StarCompanion.exe"
    ) else (
        echo.
        echo Executável não encontrado.
        echo Executando diretamente via Python...
        start /b "" pythonw "bin\executar.py"
    )
) 