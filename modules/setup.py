import os
import sys
import shutil
import subprocess
from pathlib import Path
import winreg as reg

def criar_executavel():
    # Verifica se o PyInstaller está instalado
    try:
        import PyInstaller
        print("PyInstaller já está instalado.")
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Nome do executável
    nome_app = "StarCompanion"
    
    # Pasta de saída
    pasta_dist = "dist"
    
    # Caminho do ícone (opcional)
    icone = ""
    icone_param = ""
    if os.path.exists("assets/icon.ico"):
        icone = os.path.abspath("assets/icon.ico")
        icone_param = f"--icon={icone}"
    
    # Caminho do arquivo de configuração
    config_path = os.path.abspath("assets/config/star_config.json")
    
    # Construir o executável com PyInstaller usando o módulo python -m
    print(f"Criando executável {nome_app}.exe...")
    comando = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--onefile"
    ]
    
    # Adicionar parâmetro de ícone se existir
    if icone_param:
        comando.append(icone_param)
    
    # Adicionar nome e dados
    comando.extend([
        "--name", nome_app,
        "--add-data", f"{config_path};assets/config",
        "src/main.py"
    ])
    
    print(f"Executando comando: {' '.join(comando)}")
    
    # Executar comando
    try:
        subprocess.run(comando, check=True)
        print("Executável criado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar executável: {e}")
        raise
    except FileNotFoundError as e:
        print(f"Erro: PyInstaller não encontrado. Erro detalhado: {e}")
        # Tentar com path alternativo
        try:
            print("Tentando método alternativo...")
            alt_comando = [
                sys.executable,
                "-m", "pip", "install", "pyinstaller"
            ]
            subprocess.run(alt_comando, check=True)
            
            pyinstaller_cmd = os.path.join(os.path.dirname(sys.executable), "Scripts", "pyinstaller.exe")
            if not os.path.exists(pyinstaller_cmd):
                pyinstaller_cmd = os.path.join(os.path.dirname(sys.executable), "pyinstaller.exe")
            
            if not os.path.exists(pyinstaller_cmd):
                print(f"Não foi possível encontrar o executável do PyInstaller em: {pyinstaller_cmd}")
                raise Exception("PyInstaller não encontrado após instalação")
            
            cmd_final = [pyinstaller_cmd, "--noconfirm", "--windowed", "--onefile"]
            if icone_param:
                cmd_final.append(icone_param)
            
            cmd_final.extend([
                "--name", nome_app,
                "--add-data", f"{config_path};assets/config",
                "src/main.py"
            ])
            
            print(f"Executando comando alternativo: {' '.join(cmd_final)}")
            subprocess.run(cmd_final, check=True)
        except Exception as ex:
            print(f"Também falhou com o método alternativo: {ex}")
            raise
    
    # Mover o executável para a pasta bin se não existir
    exe_dist_path = os.path.join(os.path.abspath(pasta_dist), f"{nome_app}.exe")
    bin_path = os.path.join(os.path.abspath("bin"), f"{nome_app}.exe")
    
    # Copiar o executável para a pasta bin
    if os.path.exists(exe_dist_path):
        os.makedirs("bin", exist_ok=True)
        shutil.copy2(exe_dist_path, bin_path)
        print(f"Executável copiado para a pasta bin: {bin_path}")
    
    # Retornar caminho do executável
    return exe_dist_path

def adicionar_inicializacao_automatica(caminho_exe):
    # Caminho do registro para inicialização automática
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    
    # Nome do programa no registro
    app_name = "StarCompanion"
    
    try:
        # Abrir a chave de registro
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_SET_VALUE)
        
        # Definir o valor para iniciar automaticamente
        reg.SetValueEx(key, app_name, 0, reg.REG_SZ, caminho_exe)
        
        # Fechar a chave
        reg.CloseKey(key)
        print(f"Configuração de inicialização automática adicionada para {app_name}")
        return True
    except Exception as e:
        print(f"Erro ao configurar inicialização automática: {e}")
        return False

def instalar_programa():
    try:
        # 1. Criar o executável
        caminho_exe = criar_executavel()
        
        # 2. Adicionar à inicialização automática do Windows
        if os.path.exists(caminho_exe):
            adicionar_inicializacao_automatica(caminho_exe)
            print(f"Instalação completa! O executável foi criado em: {caminho_exe}")
            print("O programa irá iniciar automaticamente sempre que você ligar o computador.")
        else:
            print(f"Erro: O executável não foi encontrado após a compilação em: {caminho_exe}")
    except Exception as e:
        print(f"Erro durante a instalação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("Iniciando instalação do StarCompanion...")
    instalar_programa() 