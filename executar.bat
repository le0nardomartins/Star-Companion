@echo off
echo Iniciando StarCompanion...
cd /d "%~dp0"

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python não encontrado! Execute primeiro o instalador (instalar.bat)
    echo.
    echo Pressione qualquer tecla para executar o instalador...
    pause >nul
    call instalar.bat
    exit /b
)

REM Verificar dependências principais
python -c "import win32gui" >nul 2>&1
if %errorlevel% neq 0 (
    echo Dependências não encontradas! Execute primeiro o instalador (instalar.bat)
    echo.
    echo Pressione qualquer tecla para executar o instalador...
    pause >nul
    call instalar.bat
    exit /b
)

if exist "bin\StarCompanion.exe" (
    start /b "" "bin\StarCompanion.exe"
) else (
    if exist "dist\StarCompanion.exe" (
        start /b "" "dist\StarCompanion.exe"
    ) else (
        echo.
        echo Executável não encontrado.
        echo Executando diretamente via Python...
        
        REM Verificar se o arquivo main.py existe
        if exist "src\main.py" (
            start /b "" pythonw "src\main.py"
        ) else (
            echo.
            echo Arquivo main.py não encontrado!
            echo Executando o instalador para reparar a instalação...
            pause
            call instalar.bat
        )
    )
) 