@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Instalador do Star Companion
echo ===================================
echo.

echo Verificando permissoes de administrador...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Este script precisa ser executado como administrador.
    echo Clique com o botao direito no arquivo e selecione "Executar como administrador".
    pause
    exit /b 1
)

echo Instalando StarCompanion...
echo.

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python não encontrado! Por favor, instale o Python 3.8 ou superior.
    echo Você pode baixá-lo em: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Verificar a versão do Python (deve ser 3.8 ou superior)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do (
    set py_version=%%V
)

set major_version=!py_version:~0,1!
set minor_version=!py_version:~2,1!

if !major_version! lss 3 (
    echo Versão do Python é menor que 3.0. Por favor, instale o Python 3.8 ou superior.
    echo.
    pause
    exit /b 1
)

if !major_version! equ 3 (
    if !minor_version! lss 8 (
        echo Versão do Python é menor que 3.8. Por favor, atualize para Python 3.8 ou superior.
        echo.
        pause
        exit /b 1
    )
)

REM Instalar dependências
echo Instalando dependências...
python -m pip install --upgrade pip
python -m pip install -r modules\requirements.txt keyboard
if %errorlevel% neq 0 (
    echo Falha ao instalar dependências.
    pause
    exit /b 1
)

REM Instalar PyInstaller separadamente para garantir
echo Instalando PyInstaller...
python -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo Falha ao instalar PyInstaller.
    pause
    exit /b 1
)

REM Executar setup.py para criar executável e configurar inicialização automática
echo Criando executável e configurando inicialização automática...
python modules\setup.py
if %errorlevel% neq 0 (
    echo Falha na instalação.
    pause
    exit /b 1
)

echo.
echo Instalação concluída com sucesso!
echo O StarCompanion será iniciado automaticamente quando você ligar o computador.
echo Para iniciar agora, execute o arquivo StarCompanion.exe na pasta bin.
echo.
echo Pressione qualquer tecla para iniciar o programa agora...
pause >nul

REM Iniciar o programa
if exist "bin\StarCompanion.exe" (
    start bin\StarCompanion.exe
) else (
    if exist "dist\StarCompanion.exe" (
        start dist\StarCompanion.exe
    ) else (
        echo Não foi possível encontrar o executável. Verifique as pastas bin e dist.
        pause
    )
)

REM Verificar se a pasta bin existe
if not exist "bin" (
    mkdir bin
)

REM Verificar se a pasta assets\config existe
if not exist "assets\config" (
    mkdir "assets\config"
)

echo Configuração concluída com sucesso!
echo.
echo Para executar o Star Companion, clique duas vezes no arquivo "executar.bat"
echo.

exit /b 0 