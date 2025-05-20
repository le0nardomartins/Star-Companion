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
    echo Python não encontrado! Iniciando download e instalação automática...
    echo.
    
    REM Criar pasta temporária para download
    if not exist "temp" mkdir temp
    
    echo Baixando Python 3.11...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe', 'temp\python-installer.exe')"
    
    if not exist "temp\python-installer.exe" (
        echo Falha ao baixar o Python. Por favor, instale manualmente.
        echo Você pode baixá-lo em: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo Instalando Python 3.11 (aguarde)...
    temp\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
    
    echo Aguardando conclusão da instalação...
    timeout /t 30 /nobreak >nul
    
    echo Verificando instalação do Python...
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Instalação do Python falhou. Por favor, reinicie o computador e tente novamente.
        pause
        exit /b 1
    )
    
    echo Python instalado com sucesso!
    echo.
)

REM Verificar a versão do Python (deve ser 3.8 ou superior)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do (
    set py_version=%%V
)

set major_version=!py_version:~0,1!
set minor_version=!py_version:~2,1!

if !major_version! lss 3 (
    echo Versão do Python é menor que 3.0. Baixando versão mais recente...
    
    REM Criar pasta temporária para download
    if not exist "temp" mkdir temp
    
    echo Baixando Python 3.11...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe', 'temp\python-installer.exe')"
    
    echo Instalando Python 3.11 (aguarde)...
    temp\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
    
    echo Aguardando conclusão da instalação...
    timeout /t 30 /nobreak >nul
    
    echo Reinicie o computador e execute este instalador novamente.
    pause
    exit /b 1
)

if !major_version! equ 3 (
    if !minor_version! lss 8 (
        echo Versão do Python é menor que 3.8. Baixando versão mais recente...
        
        REM Criar pasta temporária para download
        if not exist "temp" mkdir temp
        
        echo Baixando Python 3.11...
        powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe', 'temp\python-installer.exe')"
        
        echo Instalando Python 3.11 (aguarde)...
        temp\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
        
        echo Aguardando conclusão da instalação...
        timeout /t 30 /nobreak >nul
        
        echo Reinicie o computador e execute este instalador novamente.
        pause
        exit /b 1
    )
)

REM Verificar existência da pasta modules e requirements.txt
if not exist "modules" (
    mkdir modules
)

if not exist "modules\requirements.txt" (
    echo Criando arquivo de dependências...
    (
        echo pywin32^>=300
        echo pyautogui^>=0.9.53
        echo pyinstaller^>=5.6.2
        echo keyboard^>=0.13.5
    ) > modules\requirements.txt
)

REM Instalar dependências
echo Instalando dependências...
python -m pip install --upgrade pip
python -m pip install -r modules\requirements.txt
if %errorlevel% neq 0 (
    echo Falha ao instalar dependências. Tentando instalar uma por uma...
    
    python -m pip install pywin32
    python -m pip install pyautogui
    python -m pip install keyboard
    
    if %errorlevel% neq 0 (
        echo Falha ao instalar dependências.
        pause
        exit /b 1
    )
)

REM Instalar PyInstaller separadamente para garantir
echo Instalando PyInstaller...
python -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo Falha ao instalar PyInstaller.
    pause
    exit /b 1
)

REM Verificar se a pasta modules\setup.py existe
if not exist "modules\setup.py" (
    echo Arquivo setup.py não encontrado. Criando...
    (
        echo import os
        echo import sys
        echo import shutil
        echo from subprocess import call
        echo.
        echo def criar_executavel^(^):
        echo     print^("Criando executável..."^)
        echo     os.chdir^(os.path.dirname^(os.path.dirname^(os.path.abspath^(__file__^)^)^)^)
        echo     cmd = "pyinstaller --onefile --windowed --icon=assets/icons/star.ico --add-data assets/config;assets/config src/main.py --name StarCompanion"
        echo     os.system^(cmd^)
        echo     print^("Executável criado com sucesso!"^)
        echo.
        echo def configurar_inicializacao^(^):
        echo     print^("Configurando inicialização automática..."^)
        echo     startup_path = os.path.join^(os.getenv^('APPDATA'^), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'^)
        echo     shortcut_path = os.path.join^(startup_path, 'StarCompanion.lnk'^)
        echo     
        echo     try:
        echo         exe_path = os.path.abspath^(os.path.join^('bin', 'StarCompanion.exe'^)^)
        echo         if not os.path.exists^(exe_path^):
        echo             exe_path = os.path.abspath^(os.path.join^('dist', 'StarCompanion.exe'^)^)
        echo             
        echo         if not os.path.exists^(exe_path^):
        echo             print^("Executável não encontrado. Verifique as pastas bin e dist."^)
        echo             return False
        echo             
        echo         # Criar atalho no Startup usando PowerShell
        echo         powershell_cmd = f"""
        echo         $WshShell = New-Object -comObject WScript.Shell
        echo         $Shortcut = $WshShell.CreateShortcut^('{shortcut_path}'^)
        echo         $Shortcut.TargetPath = '{exe_path}'
        echo         $Shortcut.Save^(^)
        echo         """
        echo         
        echo         with open^('temp_script.ps1', 'w'^) as f:
        echo             f.write^(powershell_cmd^)
        echo             
        echo         os.system^('powershell -ExecutionPolicy Bypass -File temp_script.ps1'^)
        echo         
        echo         if os.path.exists^('temp_script.ps1'^):
        echo             os.remove^('temp_script.ps1'^)
        echo             
        echo         print^("Inicialização automática configurada com sucesso!"^)
        echo         return True
        echo     except Exception as e:
        echo         print^(f"Erro ao configurar inicialização automática: {e}"^)
        echo         return False
        echo.
        echo if __name__ == "__main__":
        echo     criar_executavel^(^)
        echo     configurar_inicializacao^(^)
    ) > modules\setup.py
)

REM Executar setup.py para criar executável e configurar inicialização automática
echo Criando executável e configurando inicialização automática...
python modules\setup.py
if %errorlevel% neq 0 (
    echo Falha na instalação.
    pause
    exit /b 1
)

REM Verificar se a pasta bin existe
if not exist "bin" (
    mkdir bin
)

REM Verificar se a pasta assets\config existe
if not exist "assets\config" (
    mkdir "assets\config"
)

REM Verificar se o arquivo de configuração existe
if not exist "assets\config\star_config.json" (
    echo Criando arquivo de configuração...
    (
        echo {
        echo   "janela": {
        echo     "tamanho": 64,
        echo     "particulas_tamanho": 128
        echo   },
        echo   "movimento": {
        echo     "max_velocity": 5,
        echo     "velocity_damping": 0.95,
        echo     "distancia_minima": 60,
        echo     "distancia_base": 50,
        echo     "distancia_extra_max": 70,
        echo     "aceleracao_start_distance": 300,
        echo     "desaceleracao_start_distance": 100
        echo   },
        echo   "cores": {
        echo     "normal": {
        echo       "glow": "#3A8AD3",
        echo       "inner_glow": "#A0C5FF",
        echo       "core": "#FFFFFF",
        echo       "rays": ["#A0C5FF", "#C0DFFF", "#FFFFFF"]
        echo     },
        echo     "clique": {
        echo       "glow": "#8A2BE2",
        echo       "inner_glow": "#D8BFD8",
        echo       "core": "#FFFFFF",
        echo       "rays": ["#D8BFD8", "#DDA0DD", "#EE82EE"]
        echo     },
        echo     "digitacao": {
        echo       "glow": "#FFD700",
        echo       "inner_glow": "#FFFACD",
        echo       "core": "#FFFFFF",
        echo       "rays": ["#FFFACD", "#FFEC8B", "#FFD700"]
        echo     }
        echo   },
        echo   "cores_rastro": {
        echo     "normal": ["#80B0FF", "#60A0FF", "#4080FF", "#A0D0FF", "#C0E0FF"],
        echo     "clique": ["#EE82EE", "#DDA0DD", "#DA70D6", "#D8BFD8", "#BA55D3"]
        echo   },
        echo   "efeito_clique": {
        echo     "duracao": 0.5,
        echo     "velocidade_transicao": 5.0
        echo   },
        echo   "efeito_digitacao": {
        echo     "tempo_inatividade": 0.8,
        echo     "velocidade_transicao": 3.0
        echo   },
        echo   "particulas": {
        echo     "max_rastro": 120,
        echo     "max_trail_history": 200
        echo   }
        echo }
    ) > assets\config\star_config.json
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
        echo Não foi possível encontrar o executável. Iniciando via Python...
        start pythonw src\main.py
    )
)

echo Configuração concluída com sucesso!
echo.
echo Para executar o Star Companion, clique duas vezes no arquivo "executar.bat"
echo.

exit /b 0 