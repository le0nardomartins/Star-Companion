@echo off
setlocal enabledelayedexpansion

echo =============================================
echo Encerrando todos os processos Python
echo =============================================
echo.

:: Variável para contar processos encerrados
set "processos_encerrados=0"

:: Método 1: Encerrar todos os executáveis do StarCompanion
echo Procurando e encerrando executáveis do StarCompanion...
taskkill /F /IM StarCompanion.exe >nul 2>&1
if !errorlevel! equ 0 (
    set /a "processos_encerrados+=1"
    echo - Executáveis do StarCompanion encerrados com sucesso.
) else (
    echo - Nenhum executável do StarCompanion encontrado.
)

:: Método 2: Tentar matar todos os processos Python e Pythonw diretamente
echo Encerrando todos os processos Python...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

:: Método 3: Encerrar todos os processos Python com "Python" no título da janela
echo Procurando e encerrando processos Python pelo título da janela...
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *Python*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq pythonw.exe" /FI "WINDOWTITLE eq *Python*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *StarCompanion*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq pythonw.exe" /FI "WINDOWTITLE eq *StarCompanion*" >nul 2>&1

:: Método 4: Verificar se ainda existe algum processo Python rodando
echo Verificando processos Python remanescentes...
set "pids_python="
for /f "tokens=2" %%a in ('wmic process where "name='python.exe' or name='pythonw.exe'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    set "pid=%%a"
    echo - Encerrando processo Python com PID !pid!
    taskkill /F /PID !pid! >nul 2>&1
    if !errorlevel! equ 0 set /a "processos_encerrados+=1"
)

echo.
echo Todos os processos Python foram encerrados.
echo.
timeout /t 2 > nul
exit /b 0 