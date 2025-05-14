import os
import sys
import subprocess
import threading
import keyboard

def monitorar_atalho():
    """Monitora a sequência de teclas 'qaws' para encerrar o programa"""
    keyboard.add_hotkey('qaws', lambda: os._exit(0))

def executar_programa():
    """Executa o programa principal diretamente"""
    try:
        # Iniciar o monitoramento de atalho em uma thread separada
        thread_atalho = threading.Thread(target=monitorar_atalho, daemon=True)
        thread_atalho.start()
        
        # Obter o caminho atual
        caminho_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_raiz = os.path.dirname(caminho_atual)
        
        # Verificar se o arquivo main.py existe
        caminho_main = os.path.join(caminho_raiz, 'src', 'main.py')
        if not os.path.exists(caminho_main):
            print(f"Erro: O arquivo {caminho_main} não foi encontrado.")
            return False
        
        # Verificar se o arquivo de configuração existe
        caminho_config = os.path.join(caminho_raiz, 'assets', 'config', 'star_config.json')
        if not os.path.exists(caminho_config):
            print(f"Erro: O arquivo {caminho_config} não foi encontrado.")
            return False
        
        # Executar o programa
        print("Iniciando StarCompanion diretamente...")
        subprocess.run([sys.executable, caminho_main])
        return True
    
    except Exception as e:
        print(f"Erro ao executar o programa: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if not executar_programa():
        print("\nErro ao executar o programa.")
    
    # Removendo o input para não parar a execução
    # input("\nPressione Enter para sair...") 