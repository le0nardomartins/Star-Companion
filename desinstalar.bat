@echo off
echo Desinstalando StarCompanion...
echo.

REM Remover da inicialização automática do Windows
echo Removendo da inicialização automática...
reg delete "HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "StarCompanion" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo - Registro de inicialização automática removido com sucesso.
) else (
    echo - O registro de inicialização automática não foi encontrado ou não pôde ser removido.
)

REM Verificar se o programa está em execução e finalizá-lo
echo Verificando se o programa está em execução...
taskkill /IM StarCompanion.exe /F >nul 2>&1
if %errorlevel% equ 0 (
    echo - StarCompanion foi encerrado.
) else (
    echo - StarCompanion não estava em execução.
)

REM Excluir os executáveis se existirem
echo Verificando arquivos...
if exist "bin\StarCompanion.exe" (
    del /f "bin\StarCompanion.exe" >nul 2>&1
    echo - Executável removido da pasta bin.
)

if exist "dist\StarCompanion.exe" (
    del /f "dist\StarCompanion.exe" >nul 2>&1
    echo - Executável removido da pasta dist.
) 

if not exist "bin\StarCompanion.exe" if not exist "dist\StarCompanion.exe" (
    echo - Nenhum executável encontrado para remoção.
)

echo.
echo Desinstalação concluída!
echo.
pause 