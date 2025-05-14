import os
import sys
import subprocess
import shutil
import platform

def instalar():
    print("Instalando StarCompanion...")
    
    # Verificar Python
    print("Verificando versão do Python...")
    python_version = platform.python_version_tuple()
    if int(python_version[0]) < 3 or (int(python_version[0]) == 3 and int(python_version[1]) < 7):
        print("Erro: É necessário Python 3.7 ou superior")
        return False
    
    # Atualizar pip
    print("Atualizando pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    # Instalar dependências
    print("Instalando dependências necessárias...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "modules/requirements.txt"], check=True)
    except subprocess.CalledProcessError:
        print("Erro ao instalar dependências. Tentando instalar individualmente...")
        # Tentar instalar individualmente
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pywin32>=300"], check=True)
            subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui>=0.9.53"], check=True)
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller>=5.6.2"], check=True)
        except Exception as e:
            print(f"Erro ao instalar dependências: {e}")
            return False
    
    # Importar o módulo setup para criar o executável
    try:
        sys.path.append(os.path.abspath('modules'))
        import setup
        setup.instalar_programa()
    except ImportError:
        print("Erro: O arquivo setup.py não foi encontrado em modules/setup.py")
        return False
    except Exception as e:
        print(f"Erro ao executar setup.py: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verificar se o executável foi criado
    if os.path.exists("bin/StarCompanion.exe"):
        print("\nInstalação concluída com sucesso!")
        print("O StarCompanion será iniciado automaticamente quando você ligar o computador.")
        
        # Perguntar se deseja iniciar agora
        iniciar = input("Deseja iniciar o programa agora? (S/N): ").strip().lower()
        if iniciar == 's':
            try:
                subprocess.Popen(["bin/StarCompanion.exe"])
                print("StarCompanion iniciado!")
            except Exception as e:
                print(f"Erro ao iniciar o programa: {e}")
        
        return True
    else:
        print("Erro: O executável não foi criado em bin/StarCompanion.exe.")
        if os.path.exists("dist/StarCompanion.exe"):
            print("Porém, foi encontrado em dist/StarCompanion.exe.")
            return True
        return False

if __name__ == "__main__":
    try:
        if instalar():
            print("\nInstalação concluída com sucesso!")
        else:
            print("\nA instalação falhou.")
    except Exception as e:
        print(f"Erro durante a instalação: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPressione Enter para sair...") 