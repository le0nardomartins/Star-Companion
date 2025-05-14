import tkinter as tk
from win32api import GetCursorPos, GetKeyState
import time
import threading
import math
import random
import sys
import json
import pyautogui
import os

class MouseFollower:
    def __init__(self):
        """Inicializa a aplicação"""
        # Carregar configurações do arquivo JSON
        try:
            # Ajustar caminho do arquivo de configuração quando for executado como exe
            if getattr(sys, 'frozen', False):
                # Se for executado como um executável
                base_path = sys._MEIPASS
                config_path = os.path.join(base_path, 'assets', 'config', 'star_config.json')
            else:
                # Se for executado como script
                base_path = os.path.dirname(os.path.abspath(__file__))
                root_path = os.path.dirname(base_path)
                config_path = os.path.join(root_path, 'assets', 'config', 'star_config.json')
            
            # Verificar se o arquivo de configuração existe
            if not os.path.exists(config_path):                
                # Tentar encontrar o arquivo em outras localizações comuns
                possibles_paths = [
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'star_config.json'),
                    'star_config.json',
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'star_config.json'),
                    os.path.join(os.getcwd(), 'star_config.json'),
                    os.path.join(os.getcwd(), 'assets', 'config', 'star_config.json')
                ]
                
                for path in possibles_paths:
                    if os.path.exists(path):
                        config_path = path
                        break
                
                if not os.path.exists(config_path):
                    raise FileNotFoundError(f"Não foi possível encontrar o arquivo de configuração star_config.json em nenhum local conhecido.")
            
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            sys.exit(1)
        
        # Configurar a janela principal
        self.root = tk.Tk()
        self.window_size = self.config['janela']['tamanho']
        self.root.geometry(f"{self.window_size}x{self.window_size}")
        self.root.overrideredirect(True)  # Remover bordas da janela
        self.root.attributes("-topmost", True)  # Manter no topo
        self.root.attributes('-transparentcolor', '#000000')  # Fundo transparente
        self.root.configure(bg='#000000')  # Cor de fundo preta (que será transparente)
        
        # Configurar a janela secundária para partículas/efeitos
        self.particles_window = tk.Toplevel(self.root)
        self.particles_window_size = self.config['janela']['particulas_tamanho']
        self.particles_window.geometry(f"{self.particles_window_size}x{self.particles_window_size}")
        self.particles_window.overrideredirect(True)  # Remover bordas
        self.particles_window.attributes("-topmost", True)  # Manter no topo
        self.particles_window.attributes('-transparentcolor', '#000000')  # Fundo transparente
        self.particles_window.configure(bg='#000000')  # Cor de fundo preta (que será transparente)
        
        # Definir a mesma posição inicial para ambas as janelas para evitar desalinhamento inicial
        self.particles_window.update_idletasks()  # Forçar atualização para consistência
        
        # Canvas principal para a estrela
        self.center_x = self.window_size // 2
        self.center_y = self.window_size // 2
        self.canvas = tk.Canvas(
            self.root, width=self.window_size, height=self.window_size,
            bg='#000000', highlightthickness=0
        )
        self.canvas.pack()
        
        # Canvas secundário para partículas e rastros
        self.particles_center_x = self.particles_window_size // 2
        self.particles_center_y = self.particles_window_size // 2
        self.particles_canvas = tk.Canvas(
            self.particles_window, width=self.particles_window_size, height=self.particles_window_size,
            bg='#000000', highlightthickness=0
        )
        self.particles_canvas.pack()
        
        # Variáveis para rastrear posição da estrela
        self.current_star_x = 0
        self.current_star_y = 0
        self.last_star_x = 0
        self.last_star_y = 0
        
        # Velocidade da estrela (para efeito de inércia)
        self.star_velocity_x = 0
        self.star_velocity_y = 0
        self.max_velocity = self.config['movimento']['max_velocity']
        self.velocity_damping = self.config['movimento']['velocity_damping']
        
        # Desenhar a estrela no canvas principal
        self.star_id = self.canvas.create_oval(
            self.center_x - 2, self.center_y - 2,
            self.center_x + 2, self.center_y + 2,
            fill='#80B0FF', outline="#C0E0FF", width=1
        )
        
        # Raios da estrela (inicialmente invisíveis)
        self.rays = []
        self.criar_raios()
        
        # Lista para armazenar as partículas de rastro
        self.rastro = []
        self.max_rastro = 120  # Número máximo de partículas no rastro aumentado para 120 (era 80)
        self.vida_rastro = 5.0  # Vida em segundos das partículas do rastro
        
        # Lista para partículas de brilho
        self.particulas_brilho = []
        self.max_particulas = 80  # Número máximo de partículas de brilho
        self.vida_brilho_estatico = 0.8  # Vida aumentada de 0.5 para 0.8
        self.vida_brilho_rastro = 0.2  # Vida aumentada de 0.01 para 0.2
        
        # Controles para seguir o mouse
        self.running = True
        self.last_mouse_positions = []  # Histórico de posições do mouse
        self.last_move_time = time.time()  # Último momento em que o mouse se moveu
        self.modo_manobra_random = False  # Modo de movimento aleatório quando o mouse está parado
        
        # Distâncias para o novo comportamento de movimento
        self.distancia_base = 50      # Distância base aumentada de 30 para 50
        self.distancia_extra_max = 70 # Distância extra máxima aumentada de 50 para 70
        self.min_distance = 60  # Distância mínima do cursor aumentada de 37 para 60
        self.zona_critica = 40  # Nova zona crítica: quando o cursor chega a esta distância, aciona manobra de emergência
        self.aceleracao_start_distance = 300  # Distância onde começa a aceleração
        self.desaceleracao_start_distance = 100  # Distância onde começa a desaceleração
        
        # Velocidade de movimento da estrela
        self.velocidade_base = 0.1    # Velocidade base (movimento suave)
        self.velocidade_max = 0.3     # Velocidade máxima quando precisa se mover rápido
        self.aceleracao_distante = 8.0  # Fator de aceleração quando está muito longe do cursor
        
        # Controle de posição do cursor
        self.last_cursor_x = 0
        self.last_cursor_y = 0
        
        # Velocidade de fuga da estrela
        self.escape_speed = 2.2  # Aumentado para a estrela ser mais ágil
        
        # Para calcular a velocidade do cursor
        self.last_movement_time = time.time()
        self.cursor_speed_x = 0
        self.cursor_speed_y = 0
        
        # Histórico de posições do cursor para prever movimento
        self.cursor_history = []
        self.max_history = 5
        
        # Modo de fuga (0 = normal, 1 = evasão lateral em elipse)
        self.evasion_mode = 0
        self.evasion_direction = 1  # 1 = sentido horário, -1 = anti-horário
        self.evasion_time = 0
        self.evasion_start_angle = 0  # Ângulo inicial da evasão
        self.evasion_target_angle = 0  # Ângulo final a atingir
        self.evasion_progress = 0  # Progresso da evasão (0 a 1)
        self.evasion_start_x = 0  # Posição inicial da estrela no início da evasão
        self.evasion_start_y = 0  # Posição inicial da estrela no início da evasão
        
        # Para detectar mouse parado
        self.last_mouse_move_time = time.time()
        self.is_mouse_stationary = False
        self.random_maneuver_mode = False
        self.max_random_distance = 100  # Distância máxima para manobras aleatórias
        self.random_target_x = 0
        self.random_target_y = 0
        self.next_random_time = 0
        
        # Para criar o rastro de luz
        self.trail_positions = []  # Armazena posições recentes da estrela
        self.max_trail_length = 200  # Tamanho máximo do rastro aumentado para 200px (era 100px)
        self.trail_particles = []  # Armazena os elementos visuais do rastro
        self.min_speed_for_trail = 40  # Velocidade mínima para criar rastro (reduzida)
        self.last_trail_time = 0  # Momento da última criação de rastro
        self.is_moving_fast = False  # Flag para identificar movimento rápido
        self.trail_history = [] # Para armazenar as últimas posições da estrela
        self.max_trail_history = 200 # Número máximo de posições armazenadas aumentado para 200 (era 100)
        
        # Para partículas brilhantes ao redor da estrela
        self.ultimo_brilho = 0  # Tempo da última criação de partícula
        self.intervalo_brilho = 0.05  # Intervalo para emitir novas partículas
        
        # Parâmetros para a manobra elíptica de evasão
        self.fazendo_evasao = False  # Se está atualmente executando uma manobra de evasão
        self.angulo_evasao = 0  # Ângulo atual da evasão
        self.tempo_inicio_evasao = 0  # Quando a manobra de evasão começou
        self.duracao_evasao = 0.15  # Reduzida para ser ainda mais rápida (era 0.2)
        self.centro_evasao_x = 0  # Centro da elipse para evasão
        self.centro_evasao_y = 0  # Centro da elipse para evasão
        self.raio_evasao_a = 0  # Raio maior da elipse
        self.raio_evasao_b = 0  # Raio menor da elipse
        self.direcao_evasao = 1  # 1 = sentido horário, -1 = anti-horário
        self.angulo_cursor = 0  # Ângulo da posição do cursor em relação à estrela
        self.pos_final_evasao_x = 0  # Posição final desejada após a evasão
        self.pos_final_evasao_y = 0  # Posição final desejada após a evasão
        self.velocidade_cursor = 0  # Velocidade atual do cursor para detecção de movimento rápido
        self.abordagem_frontal = False  # Se o cursor está se aproximando frontalmente
        self.abordagem_lateral = False  # Se o cursor está se aproximando lateralmente
        
        # Criar os elementos da estrela
        self.create_star_elements()
        
        # Contador para a animação
        self.animate_counter = 0
        
        # Define a posição inicial da estrela fora da tela
        self.current_star_x = -100
        self.current_star_y = -100
        
        # Variáveis para controle de estados
        self.cor_clique_ativa = False
        self.cor_digitacao_ativa = False
        self.tempo_inicio_clique = 0
        self.tempo_ultima_digitacao = 0
        self.duracao_cor_clique = self.config['efeito_clique']['duracao']
        self.tempo_inatividade = self.config['efeito_digitacao']['tempo_inatividade']
        self.transicao_cor = 0.0  # 0.0 é azul, 1.0 é violeta/dourado
        self.velocidade_transicao = self.config['efeito_clique']['velocidade_transicao']
        self.velocidade_transicao_digitacao = self.config['efeito_digitacao']['velocidade_transicao']
        
        # Cores originais (azul)
        self.cores_originais = self.config['cores']['normal']
        
        # Cores para o clique (violeta)
        self.cores_clique = self.config['cores']['clique']
        
        # Cores para digitação (dourado)
        self.cores_digitacao = self.config['cores']['digitacao']
        
        # Estado atual da cor
        self.estado_cor_atual = "normal"  # normal, clique, ou digitacao
        
        # Variáveis para controle de animação quando mouse fica parado
        self.tempo_mouse_parado = 0
        self.tempo_para_animacao = 10.0  # 10 segundos parado para iniciar animação especial
        self.em_animacao_especial = False
        self.fase_animacao = 0  # 0=rotação, 1=aproximação, 2=afastamento rápido
        self.angulo_animacao = 0
        self.raio_animacao = 80  # Raio inicial da rotação
        self.velocidade_rotacao = 2.0  # Velocidade da rotação
        self.tempo_fase_animacao = 0
        self.target_x_animacao = 0
        self.target_y_animacao = 0
        self.ultimo_tempo_animacao = 0
        
        # Iniciar thread de monitoramento global de mouse e teclado
        self.thread_mouse_keyboard = threading.Thread(target=self.monitorar_mouse_teclado, daemon=True)
        self.thread_mouse_keyboard.start()
        
        # Iniciar thread de monitoramento de inatividade
        self.thread_monitoramento = threading.Thread(target=self.monitorar_inatividade, daemon=True)
        self.thread_monitoramento.start()
        
    def create_star_elements(self):
        """Criar os elementos da estrela"""
        # Camadas de brilho circular (azul) - agora com apenas 1 círculo (removidos os 2 mais externos)
        self.glow_sizes = [4]  # Mantido apenas o círculo mais interno
        self.glow_colors = ["#3A8AD3"]  # Cor para o círculo
        self.glow_stipples = ["gray25"]  # Tornar círculo mais transparente
        self.glows = []
        
        for i, size in enumerate(self.glow_sizes):
            glow = self.canvas.create_oval(
                self.center_x - size,
                self.center_y - size,
                self.center_x + size,
                self.center_y + size,
                fill=self.glow_colors[i], outline="", stipple=self.glow_stipples[i]
            )
            self.glows.append(glow)
        
        # Brilho interno (branco-azulado) - também mais transparente
        self.inner_glow_size = 3  # Reduzido em ~3x
        self.inner_glow = self.canvas.create_oval(
            self.center_x - self.inner_glow_size,
            self.center_y - self.inner_glow_size,
            self.center_x + self.inner_glow_size,
            self.center_y + self.inner_glow_size,
            fill="#A0C5FF", outline="", stipple="gray25"  # Adicionado stipple para mais transparência
        )
        
        # Núcleo branco
        self.core_size = 2  # Reduzido em ~3x
        self.core = self.canvas.create_oval(
            self.center_x - self.core_size,
            self.center_y - self.core_size,
            self.center_x + self.core_size,
            self.center_y + self.core_size,
            fill="#FFFFFF", outline=""
        )
        
        # Criar raios horizontais e verticais
        self.create_cross_rays()
    
    def create_cross_rays(self):
        """Criar raios em forma de cruz que pulsam"""
        # Raios horizontais e verticais (3 camadas cada)
        self.h_rays = []
        self.v_rays = []
        
        # Tamanhos e cores dos raios (reduzidos em ~3x)
        ray_widths = [self.window_size // 2 - 2, self.window_size // 3, 5]
        ray_heights = [1, 1, 1]
        ray_colors = ["#A0C5FF", "#C0DFFF", "#FFFFFF"]
        
        # Criar raios horizontais com 3 tamanhos
        for i in range(3):
            h_ray = self.canvas.create_rectangle(
                self.center_x - ray_widths[i],
                self.center_y - ray_heights[i]//2,
                self.center_x + ray_widths[i],
                self.center_y + ray_heights[i]//2,
                fill=ray_colors[i], outline=""
            )
            self.h_rays.append(h_ray)
            
            v_ray = self.canvas.create_rectangle(
                self.center_x - ray_heights[i]//2,
                self.center_x - ray_widths[i],
                self.center_x + ray_heights[i]//2,
                self.center_x + ray_widths[i],
                fill=ray_colors[i], outline=""
            )
            self.v_rays.append(v_ray)
    
    def criar_raios(self):
        """Cria os raios da estrela"""
        # Limpar raios existentes
        for ray in self.rays:
            self.canvas.delete(ray)
        self.rays = []
        
        # Número de raios
        num_raios = 8
        
        # Tamanho dos raios
        tamanho_base = 8  # Tamanho base dos raios
        
        # Cores dos raios (do mais externo ao mais interno)
        cores = ["#80B0FF", "#A0C5FF", "#FFFFFF"]
        
        # Criar os raios em diferentes ângulos
        for i in range(num_raios):
            angulo = i * (math.pi / 4)  # 8 raios igualmente espaçados (45 graus)
            
            # Para cada ângulo, criar 3 raios de cores e tamanhos diferentes
            for j, cor in enumerate(cores):
                # Tamanho diminui do externo para o interno
                tamanho = tamanho_base * (3 - j) / 3
                
                # Calcular pontos inicial e final do raio
                x1 = self.center_x + math.cos(angulo) * 2  # Começa longe do centro
                y1 = self.center_y + math.sin(angulo) * 2
                x2 = self.center_x + math.cos(angulo) * tamanho
                y2 = self.center_y + math.sin(angulo) * tamanho
                
                # Criar uma linha para representar o raio
                ray = self.canvas.create_line(x1, y1, x2, y2, fill=cor, width=1)
                self.rays.append(ray)
                
    def update_animation(self, dt):
        """Atualiza a animação da estrela (pulsação dos raios e brilho)"""
        try:
            # Incrementar contador de animação
            self.animate_counter += dt * 5  # Velocidade da animação aumentada (era 3)
            
            # Fator de pulsação para os raios (entre 0.85 e 1.15) - aumentado
            pulse_factor = 1.0 + 0.15 * math.sin(self.animate_counter)  # Amplitude da pulsação aumentada
            
            # Número de raios e camadas
            num_raios = 8
            num_camadas = 3
            
            # Tamanho dos raios
            tamanho_base = 8
            
            # Obter as cores atuais com base na transição
            cores_atuais = self.obter_cores_atuais()
            
            # Atualizar a posição dos raios (pulsar)
            for i in range(num_raios):
                angulo = i * (math.pi / 4)
                
                for j in range(num_camadas):
                    # Índice do raio atual
                    ray_index = i * num_camadas + j
                    
                    if ray_index < len(self.rays):
                        # Tamanho diminui do externo para o interno
                        tamanho = tamanho_base * (3 - j) / 3
                        
                        # Aplicar efeito de pulsação
                        tamanho_atual = tamanho * pulse_factor
                        
                        # Calcular pontos inicial e final do raio
                        x1 = self.center_x + math.cos(angulo) * 2  # Começa longe do centro
                        y1 = self.center_y + math.sin(angulo) * 2
                        x2 = self.center_x + math.cos(angulo) * tamanho_atual
                        y2 = self.center_y + math.sin(angulo) * tamanho_atual
                        
                        # Atualizar a posição do raio
                        self.canvas.coords(self.rays[ray_index], x1, y1, x2, y2)
                        
                        # Atualizar a cor do raio com base na transição
                        cor_indice = j % 3
                        if cor_indice < len(cores_atuais["rays"]):
                            self.canvas.itemconfig(self.rays[ray_index], fill=cores_atuais["rays"][cor_indice])
            
            # Animar o núcleo da estrela e seu brilho
            # Atualizar tamanho do brilho interno com base na pulsação
            core_pulse = 1.0 + 0.2 * math.sin(self.animate_counter)  # Pulsação aumentada
            
            # Atualizar os círculos de brilho
            for i, glow in enumerate(self.glows):
                # Aplicar pulsação com tamanho base diferente para cada círculo
                size = self.glow_sizes[i] * core_pulse
                self.canvas.coords(
                    glow,
                    self.center_x - size,
                    self.center_y - size,
                    self.center_x + size,
                    self.center_y + size
                )
                # Manter a transparência gradual durante a pulsação
                self.canvas.itemconfig(glow, stipple=self.glow_stipples[i], fill=cores_atuais["glow"])
            
            # Atualizar o brilho interno e o núcleo
            # Brilho interno
            inner_size = 3 * core_pulse
            self.canvas.coords(
                self.inner_glow,
                self.center_x - inner_size,
                self.center_y - inner_size,
                self.center_x + inner_size,
                self.center_y + inner_size
            )
            self.canvas.itemconfig(self.inner_glow, fill=cores_atuais["inner_glow"])
            
            # Núcleo
            core_size = 2 * core_pulse
            self.canvas.coords(
                self.core,
                self.center_x - core_size,
                self.center_y - core_size,
                self.center_x + core_size,
                self.center_y + core_size
            )
            self.canvas.itemconfig(self.core, fill=cores_atuais["core"])
            
            # Atualizar a pulsação dos raios em cruz
            if hasattr(self, 'h_rays') and hasattr(self, 'v_rays'):
                # Fator de pulsação para os raios horizontais/verticais (entre 0.9 e 1.1) - aumentado
                h_pulse = 1.0 + 0.15 * math.sin(self.animate_counter * 0.7)  # Amplitude aumentada
                
                # Tamanhos base
                ray_widths = [self.window_size // 2 - 2, self.window_size // 3, 5]
                ray_heights = [1, 1, 1]
                
                # Atualizar raios horizontais
                for i in range(len(self.h_rays)):
                    # Aplicar pulsação na largura
                    width = ray_widths[i] * h_pulse
                    
                    self.canvas.coords(
                        self.h_rays[i],
                        self.center_x - width,
                        self.center_y - ray_heights[i]//2,
                        self.center_x + width,
                        self.center_y + ray_heights[i]//2
                    )
                    # Atualizar a cor do raio
                    if i < len(cores_atuais["rays"]):
                        self.canvas.itemconfig(self.h_rays[i], fill=cores_atuais["rays"][i])
                    
                    # Atualizar raios verticais
                    self.canvas.coords(
                        self.v_rays[i],
                        self.center_x - ray_heights[i]//2,
                        self.center_y - width,
                        self.center_x + ray_heights[i]//2,
                        self.center_y + width
                    )
                    # Atualizar a cor do raio
                    if i < len(cores_atuais["rays"]):
                        self.canvas.itemconfig(self.v_rays[i], fill=cores_atuais["rays"][i])
            
        except Exception as e:
            print(f"Erro na animação: {e}")
            
    def obter_cores_atuais(self):
        """Retorna as cores atuais baseadas no estado de transição"""
        try:
            cores_destino = None
            
            # Determinar qual conjunto de cores usar
            if self.estado_cor_atual == "clique":
                cores_destino = self.cores_clique
            elif self.estado_cor_atual == "digitacao":
                cores_destino = self.cores_digitacao
            
            # Se não estiver em transição, retornar cores originais
            if self.transicao_cor <= 0.01 or cores_destino is None:
                return self.cores_originais
            
            # Se transição estiver completa, retornar cores de destino
            if self.transicao_cor >= 0.99:
                return cores_destino
            
            # Fazer interpolação entre cores
            cores_atuais = {}
            
            # Função para interpolar cores hexadecimais
            def interpolar_cor(cor1, cor2, fator):
                r1, g1, b1 = int(cor1[1:3], 16), int(cor1[3:5], 16), int(cor1[5:7], 16)
                r2, g2, b2 = int(cor2[1:3], 16), int(cor2[3:5], 16), int(cor2[5:7], 16)
                
                r = int(r1 + (r2 - r1) * fator)
                g = int(g1 + (g2 - g1) * fator)
                b = int(b1 + (b2 - b1) * fator)
                
                return f"#{r:02x}{g:02x}{b:02x}"
            
            # Interpolar glow
            cores_atuais["glow"] = interpolar_cor(
                self.cores_originais["glow"], 
                cores_destino["glow"], 
                self.transicao_cor
            )
            
            # Interpolar inner_glow
            cores_atuais["inner_glow"] = interpolar_cor(
                self.cores_originais["inner_glow"], 
                cores_destino["inner_glow"], 
                self.transicao_cor
            )
            
            # O núcleo branco permanece branco
            cores_atuais["core"] = self.cores_originais["core"]
            
            # Interpolar cores dos raios
            cores_atuais["rays"] = []
            for i in range(len(self.cores_originais["rays"])):
                cor_interpolada = interpolar_cor(
                    self.cores_originais["rays"][i], 
                    cores_destino["rays"][i], 
                    self.transicao_cor
                )
                cores_atuais["rays"].append(cor_interpolada)
            
            return cores_atuais
                
        except Exception as e:
            return self.cores_originais
            
    def atualizar_cor_clique(self, dt):
        """Atualiza a transição de cor quando o clique é ativado"""
        try:
            tempo_atual = time.time()
            
            # Se o modo de cor de clique está ativo
            if self.cor_clique_ativa:
                # Verificar se já passou o tempo de duração da cor de clique
                if tempo_atual - self.tempo_inicio_clique > self.duracao_cor_clique:
                    self.cor_clique_ativa = False
                    self.estado_cor_atual = "normal"
                    self.transicao_cor = 0.0
                else:
                    # Aumentar a transição para a cor de clique de forma mais gradual
                    self.transicao_cor = min(1.0, self.transicao_cor + dt * self.velocidade_transicao * 0.7)
                    self.estado_cor_atual = "clique"
            elif self.cor_digitacao_ativa:
                # Transição para cor dourada de forma mais gradual
                self.transicao_cor = min(1.0, self.transicao_cor + dt * self.velocidade_transicao_digitacao * 0.7)
                self.estado_cor_atual = "digitacao"
            else:
                # Diminuir a transição para voltar à cor original de forma mais gradual
                self.transicao_cor = max(0.0, self.transicao_cor - dt * self.velocidade_transicao * 0.5)
                self.estado_cor_atual = "normal"
            
            # Forçar atualização das cores - chamar a animação diretamente para aplicar as cores
            self.update_animation(dt)
            
        except Exception as e:
            print(f"Erro ao atualizar cor: {e}")
    
    def follow_mouse(self, dt):
        """Atualiza a posição da estrela com base na posição do mouse"""
        try:
            # Obter a posição atual do cursor
            cursor_x = self.root.winfo_pointerx()
            cursor_y = self.root.winfo_pointery()
            
            # Verificar se o mouse está parado
            if hasattr(self, 'last_cursor_x') and hasattr(self, 'last_cursor_y'):
                if abs(cursor_x - self.last_cursor_x) < 3 and abs(cursor_y - self.last_cursor_y) < 3:
                    # Mouse parado
                    self.tempo_mouse_parado += dt
                    if self.tempo_mouse_parado >= self.tempo_para_animacao and not self.em_animacao_especial:
                        # Iniciar animação especial depois de 10 segundos parado
                        self.em_animacao_especial = True
                        self.fase_animacao = 0
                        # Iniciar a partir da posição atual para não teleportar
                        dx = self.current_star_x - cursor_x
                        dy = self.current_star_y - cursor_y
                        self.raio_animacao = math.sqrt(dx*dx + dy*dy)
                        self.angulo_animacao = math.atan2(dy, dx)
                        self.tempo_fase_animacao = 0
                        self.ultimo_tempo_animacao = time.time()
                        # Inicializar variáveis de controle de última posição
                        self.last_target_x = self.current_star_x
                        self.last_target_y = self.current_star_y
                else:
                    # Mouse moveu, resetar contador
                    self.tempo_mouse_parado = 0
                    if self.em_animacao_especial:
                        # Desativar a animação, mas guardar a posição atual para transição suave
                        if self.fase_animacao != 3:
                            # Guardar a posição atual como ponto de referência para suavizar o retorno
                            if hasattr(self, 'last_target_x') and hasattr(self, 'last_target_y'):
                                self.target_x_animacao = self.last_target_x
                                self.target_y_animacao = self.last_target_y
                            self.em_animacao_especial = False
            
            # Obter informações da tela usando o objeto root do Tkinter
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Verificar se o cursor está fora dos limites da tela atual
            cursor_fora_limites = (
                cursor_x <= 0 or 
                cursor_x >= screen_width - 5 or 
                cursor_y <= 0 or 
                cursor_y >= screen_height - 5
            )
            
            # Detectar mudança brusca de monitor (teleporte do cursor)
            mudanca_brusca = False
            if self.last_cursor_x != 0 and self.last_cursor_y != 0:
                distancia_cursor = math.sqrt((cursor_x - self.last_cursor_x)**2 + (cursor_y - self.last_cursor_y)**2)
                if distancia_cursor > 200:  # Distância grande indica mudança de monitor
                    mudanca_brusca = True
            
            # Se o cursor estiver fora dos limites ou houve mudança brusca
            if cursor_fora_limites or mudanca_brusca:
                # Manter a estrela onde está, apenas desacelerar suavemente
                self.star_velocity_x *= 0.8
                self.star_velocity_y *= 0.8
                target_x = self.current_star_x
                target_y = self.current_star_y
            elif self.em_animacao_especial:
                # Realizar a animação especial quando o mouse está parado
                target_x, target_y = self.animar_estrela_parada(cursor_x, cursor_y, dt)
            elif self.modo_manobra_random:
                # Modo de manobra aleatória - mover em padrões imprevisíveis ao redor do cursor, 
                # mas mantendo distância mínima
                angulo = time.time() * 2  # Ângulo baseado no tempo para movimento circular
                raio = max(self.config['movimento']['distancia_minima'], 20 + 15 * math.sin(time.time() * 1.5))  # Raio variável, mas sempre maior que min_distance
                
                target_x = cursor_x + raio * math.cos(angulo)
                target_y = cursor_y + raio * math.sin(angulo)
                
                # Adicionar pequenos movimentos aleatórios para parecer mais natural
                # mas verificar se a distância final continua maior que o mínimo
                random_x = random.uniform(-5, 5)
                random_y = random.uniform(-5, 5)
                
                # Verificar se a aleatoriedade não vai fazer a estrela ficar muito perto do cursor
                new_dist = math.sqrt((target_x + random_x - cursor_x)**2 + (target_y + random_y - cursor_y)**2)
                if new_dist >= self.config['movimento']['distancia_minima']:
                    target_x += random_x
                    target_y += random_y
            else:
                # Se a estrela ainda não tem posição inicial, colocá-la próxima ao cursor
                if self.current_star_x < -50 or self.current_star_y < -50:
                    # Posição inicial a min_distance pixels do cursor em uma direção aleatória
                    angulo_inicial = random.uniform(0, math.pi * 2)
                    self.current_star_x = cursor_x + math.cos(angulo_inicial) * self.config['movimento']['distancia_minima']
                    self.current_star_y = cursor_y + math.sin(angulo_inicial) * self.config['movimento']['distancia_minima']
                    
                    # Reset das velocidades
                    self.star_velocity_x = 0
                    self.star_velocity_y = 0
                
                # Calcular vetor do cursor para a estrela
                dx = self.current_star_x - cursor_x
                dy = self.current_star_y - cursor_y
                
                # Calcular distância atual entre o cursor e a estrela
                distancia_atual = math.sqrt(dx*dx + dy*dy)
                
                # Normalizar o vetor se não for zero
                if distancia_atual > 0:
                    dx /= distancia_atual
                    dy /= distancia_atual
                else:
                    # Se a distância for zero, mover em uma direção aleatória
                    angulo = random.uniform(0, math.pi * 2)
                    dx = math.cos(angulo)
                    dy = math.sin(angulo)
                
                # Determinar a distância desejada baseada na velocidade do mouse
                distancia_desejada = max(self.config['movimento']['distancia_minima'], self.config['movimento']['distancia_base']) # Garantir distância mínima
                
                if len(self.last_mouse_positions) >= 2:
                    # Calcular a velocidade do mouse
                    pos_antiga = self.last_mouse_positions[0]
                    pos_atual = self.last_mouse_positions[-1]
                    
                    delta_x = pos_atual[0] - pos_antiga[0]
                    delta_y = pos_atual[1] - pos_antiga[1]
                    
                    velocidade_mouse = math.sqrt(delta_x*delta_x + delta_y*delta_y) / len(self.last_mouse_positions)
                    
                    # Limitar a velocidade máxima do mouse para evitar comportamentos erráticos em mudanças de monitor
                    velocidade_mouse = min(velocidade_mouse, 150)
                    
                    # Ajustar a distância desejada baseada na velocidade do mouse
                    # Quando o mouse se move rápido, a estrela fica mais longe, mas nunca menos que min_distance
                    extra_distance = min(velocidade_mouse * 1.5, self.config['movimento']['distancia_extra_max'])
                    distancia_desejada = max(self.config['movimento']['distancia_minima'], self.config['movimento']['distancia_base'] + extra_distance)
                
                # Calcular a posição alvo
                target_x = cursor_x + dx * distancia_desejada
                target_y = cursor_y + dy * distancia_desejada
                
                # Verificar novamente se a distância final é maior que o mínimo
                final_dist = math.sqrt((target_x - cursor_x)**2 + (target_y - cursor_y)**2)
                if final_dist < self.config['movimento']['distancia_minima']:
                    # Ajustar para manter a distância mínima
                    factor = self.config['movimento']['distancia_minima'] / final_dist
                    target_x = cursor_x + (target_x - cursor_x) * factor
                    target_y = cursor_y + (target_y - cursor_y) * factor
                
                # Implementar aceleração quando o mouse está muito longe
                distancia_atual = math.sqrt((self.current_star_x - cursor_x)**2 + (self.current_star_y - cursor_y)**2)
                
                # Se a distância for maior que a distância crítica, aplicar aceleração
                if distancia_atual > self.config['movimento']['aceleracao_start_distance']:
                    # Calcular fator de aceleração (0 a 1)
                    fator_aceleracao = min(1.0, (distancia_atual - self.config['movimento']['aceleracao_start_distance']) / 200)
                    
                    # Calcular direção para o cursor
                    dir_x = cursor_x - self.current_star_x
                    dir_y = cursor_y - self.current_star_y
                    dist = math.sqrt(dir_x*dir_x + dir_y*dir_y)
                    
                    if dist > 0:
                        dir_x /= dist
                        dir_y /= dist
                        
                        # Aplicar aceleração na direção do cursor
                        aceleracao = self.config['movimento']['aceleracao_distante'] * fator_aceleracao
                        self.star_velocity_x += dir_x * aceleracao * dt
                        self.star_velocity_y += dir_y * aceleracao * dt
                        
                        # Limitar velocidade máxima
                        velocidade_atual = math.sqrt(self.star_velocity_x**2 + self.star_velocity_y**2)
                        if velocidade_atual > self.config['movimento']['max_velocity']:
                            fator_limite = self.config['movimento']['max_velocity'] / velocidade_atual
                            self.star_velocity_x *= fator_limite
                            self.star_velocity_y *= fator_limite
                else:
                    # Desacelerar quando estiver próximo da distância desejada
                    self.star_velocity_x *= self.config['movimento']['velocity_damping']
                    self.star_velocity_y *= self.config['movimento']['velocity_damping']
                
                # Aplicar a velocidade à posição alvo
                target_x += self.star_velocity_x
                target_y += self.star_velocity_y
            
            # Garantir que a estrela não saia dos limites da tela
            target_x = max(50, min(screen_width - 50, target_x))
            target_y = max(50, min(screen_height - 50, target_y))
            
            # Atualizar a posição da estrela com suavização
            if hasattr(self, 'last_position_x') and hasattr(self, 'last_position_y'):
                # Aplicar suavização ao movimento com interpolação
                # Mais suave quando a estrela está em animação especial, menos quando segue o cursor
                smoothing_factor = 0.85 if self.em_animacao_especial else 0.7
                
                # Aplicar interpolação para suavizar o movimento
                self.current_star_x = self.last_position_x + (target_x - self.last_position_x) * (1 - smoothing_factor)
                self.current_star_y = self.last_position_y + (target_y - self.last_position_y) * (1 - smoothing_factor)
            else:
                # Caso seja a primeira vez, usar a posição diretamente
                self.current_star_x = target_x
                self.current_star_y = target_y
            
            # Armazenar as posições para a próxima interpolação
            self.last_position_x = self.current_star_x
            self.last_position_y = self.current_star_y
            
            # Atualizar a posição da janela principal (com a estrela)
            nova_x = int(self.current_star_x - self.center_x)
            nova_y = int(self.current_star_y - self.center_y)
            
            # Eliminar micro-tremores convertendo para inteiros de forma especial
            # em vez de simplesmente arredondar, para evitar oscilação de pixel
            if hasattr(self, 'last_window_x') and hasattr(self, 'last_window_y'):
                # Só mover a janela se a diferença de posição for significativa
                if abs(nova_x - self.last_window_x) >= 1 or abs(nova_y - self.last_window_y) >= 1:
                    self.root.geometry(f"{self.window_size}x{self.window_size}+{nova_x}+{nova_y}")
                    self.last_window_x = nova_x
                    self.last_window_y = nova_y
                    
                    # Atualizar também imediatamente a janela de partículas para evitar atraso
                    # Calcular a posição da janela de partículas para manter a estrela centralizada
                    offset_x = (self.particles_window_size - self.window_size) // 2
                    offset_y = (self.particles_window_size - self.window_size) // 2
                    particles_x = nova_x - offset_x
                    particles_y = nova_y - offset_y
                    self.particles_window.geometry(f"{self.particles_window_size}x{self.particles_window_size}+{particles_x}+{particles_y}")
            else:
                # Primeira vez, inicializar valores
                self.root.geometry(f"{self.window_size}x{self.window_size}+{nova_x}+{nova_y}")
                self.last_window_x = nova_x
                self.last_window_y = nova_y
                
                # Atualizar também a janela de partículas
                offset_x = (self.particles_window_size - self.window_size) // 2
                offset_y = (self.particles_window_size - self.window_size) // 2
                particles_x = nova_x - offset_x
                particles_y = nova_y - offset_y
                self.particles_window.geometry(f"{self.particles_window_size}x{self.particles_window_size}+{particles_x}+{particles_y}")
            
            # Se a estrela se mover rápido, criar um rastro de luz (exceto em mudanças de monitor)
            if len(self.last_mouse_positions) >= 2:
                dx_star = self.current_star_x - self.last_star_x
                dy_star = self.current_star_y - self.last_star_y
                velocidade_star = math.sqrt(dx_star*dx_star + dy_star*dy_star)
                
                # Reduzido o limite de velocidade para criar mais rastro (era 2)
                if velocidade_star > 0.5:  # Se a estrela estiver se movendo, mesmo que lentamente
                    self.criar_rastro()
            
            # Atualizar a última posição da estrela
            self.last_star_x = self.current_star_x
            self.last_star_y = self.current_star_y
            
            # Atualizar a última posição do cursor
            self.last_cursor_x = cursor_x
            self.last_cursor_y = cursor_y
            
        except Exception as e:
            print(f"Erro ao seguir o mouse: {e}")
    
    def criar_rastro(self, tamanho_extra=0):
        """Criar uma partícula para o rastro de luz"""
        try:
            # Armazenar a posição atual da estrela no histórico de trail
            self.trail_history.append((self.current_star_x, self.current_star_y))
            if len(self.trail_history) > self.config['particulas']['max_trail_history']:
                self.trail_history.pop(0)
            
            # Criar um pequeno círculo na posição atual da estrela - tamanho aumentado
            # Se tamanho_extra > 0, aumentar o tamanho da partícula proporcionalmente
            tamanho_base = 4.0 + tamanho_extra  # Tamanho base aumentado quando há aceleração
            tamanho_max = 7.0 + tamanho_extra * 1.5
            tamanho_particula = random.uniform(tamanho_base, tamanho_max)
            
            # Posição atual da estrela (centro)
            centro_x = self.current_star_x
            centro_y = self.current_star_y
            
            # Posição relativa ao canvas de partículas
            # Ajusta para que a posição seja relativa à janela de partículas
            offset_x = (self.particles_window_size - self.window_size) // 2
            offset_y = (self.particles_window_size - self.window_size) // 2
            
            # Posição da partícula no canvas de partículas
            pos_canvas_x = self.particles_center_x + (centro_x - self.current_star_x)
            pos_canvas_y = self.particles_center_y + (centro_y - self.current_star_y)
            
            # Adicionar uma variação aleatória na posição com distância mínima da estrela
            variacao = 3.0
            pos_x = pos_canvas_x + random.uniform(-variacao, variacao)
            pos_y = pos_canvas_y + random.uniform(-variacao, variacao)
            
            # Garantir distância mínima do centro da estrela
            dx = pos_x - pos_canvas_x
            dy = pos_y - pos_canvas_y
            distancia = math.sqrt(dx*dx + dy*dy)
            if distancia < 5:  # Mínimo de 5 pixels do centro da estrela
                # Normalizar vetor e ajustar para distância mínima
                if distancia > 0:
                    dx /= distancia
                    dy /= distancia
                else:
                    # Se distância for zero, escolher direção aleatória
                    angulo = random.uniform(0, math.pi * 2)
                    dx = math.cos(angulo)
                    dy = math.sin(angulo)
                pos_x = pos_canvas_x + dx * 5
                pos_y = pos_canvas_y + dy * 5
            
            # Selecionar cor com base na transição atual
            if self.estado_cor_atual == "clique":
                # Interpolação entre azul e violeta para o rastro
                cor_base_normal = random.choice(self.config['cores_rastro']['normal'])
                cor_base_clique = random.choice(self.config['cores_rastro']['clique'])
                r1, g1, b1 = int(cor_base_normal[1:3], 16), int(cor_base_normal[3:5], 16), int(cor_base_normal[5:7], 16)
                r2, g2, b2 = int(cor_base_clique[1:3], 16), int(cor_base_clique[3:5], 16), int(cor_base_clique[5:7], 16)
                r = int(r1 + (r2 - r1) * self.transicao_cor)
                g = int(g1 + (g2 - g1) * self.transicao_cor)
                b = int(b1 + (b2 - b1) * self.transicao_cor)
                cor = f"#{r:02x}{g:02x}{b:02x}"
            elif self.estado_cor_atual == "digitacao":
                # Interpolação entre azul e dourado para o rastro
                cor_base_normal = random.choice(self.config['cores_rastro']['normal'])
                # Cores douradas para digitação
                cor_base_digitacao = random.choice(["#FFD700", "#FFC125", "#FFB90F", "#FFA500", "#FF8C00"])
                r1, g1, b1 = int(cor_base_normal[1:3], 16), int(cor_base_normal[3:5], 16), int(cor_base_normal[5:7], 16)
                r2, g2, b2 = int(cor_base_digitacao[1:3], 16), int(cor_base_digitacao[3:5], 16), int(cor_base_digitacao[5:7], 16)
                r = int(r1 + (r2 - r1) * self.transicao_cor)
                g = int(g1 + (g2 - g1) * self.transicao_cor)
                b = int(b1 + (b2 - b1) * self.transicao_cor)
                cor = f"#{r:02x}{g:02x}{b:02x}"
            else:
                # Paleta de cores azul original para o rastro
                cor = random.choice(self.config['cores_rastro']['normal'])
            
            # Criar a partícula no canvas das partículas, usando transparência menor
            particula = {
                "id": self.particles_canvas.create_oval(
                    pos_x - tamanho_particula,
                    pos_y - tamanho_particula,
                    pos_x + tamanho_particula,
                    pos_y + tamanho_particula,
                    fill=cor, outline="", stipple=""  # Sem stipple para ficar totalmente visível
                ),
                "x": pos_x,  # Posição absoluta no canvas de partículas
                "y": pos_y,
                "screen_x": self.current_star_x,  # Posição absoluta na tela
                "screen_y": self.current_star_y,
                "tamanho": tamanho_particula,
                "alpha": random.uniform(0.6, 0.9),  # Transparência inicial aumentada (era 0.2, 0.4)
                "desvanecimento": random.uniform(0.02, 0.04),  # Taxa de desvanecimento reduzida (era 0.04, 0.07)
                "criacao": time.time(),  # Momento da criação para calcular idade
                "cor": cor  # Guardar a cor da partícula
            }
            
            self.trail_particles.append(particula)
            
            # Limitar o número máximo de partículas no rastro
            if len(self.trail_particles) > self.config['particulas']['max_rastro']:
                # Remover a mais antiga
                antiga = self.trail_particles.pop(0)
                self.particles_canvas.delete(antiga["id"])
            
            # Também criar partículas de brilho do tipo "rastro" quando a estrela está se movendo
            if random.random() < 0.9:  # Aumentado para 90% de chance (era 0.8)
                self.criar_particula_brilho(tipo_rastro=True)
            
        except Exception as e:
            print(f"Erro ao criar rastro: {e}")
            
    def atualizar_rastro(self, dt):
        """Atualizar o rastro de luz, desvanecendo as partículas"""
        particulas_para_remover = []
        
        # Obter a posição atual da janela principal
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        
        # Cálculo do offset do canvas de partículas
        offset_x = (self.particles_window_size - self.window_size) // 2
        offset_y = (self.particles_window_size - self.window_size) // 2
        
        # Verificar a velocidade do movimento para decidir se cria partículas extras de rastro
        if hasattr(self, 'last_star_x') and hasattr(self, 'last_star_y'):
            dx = self.current_star_x - self.last_star_x
            dy = self.current_star_y - self.last_star_y
            velocidade = math.sqrt(dx*dx + dy*dy)
            
            # Se o movimento for rápido, criar mais partículas de rastro entre pontos
            # mas apenas se distância total percorrida não ultrapassar limites
            if velocidade > 3 and velocidade <= 100 and random.random() < 0.5:  # Aumentado para 100px (era 40)
                # Interpolar pontos entre a posição anterior e a atual
                for i in range(1, 4):  # Criar 3 pontos intermediários 
                    fator = i / 4.0
                    pos_x = self.last_star_x + dx * fator
                    pos_y = self.last_star_y + dy * fator
                    
                    # Calcular distância da posição intermediária até a posição atual da estrela
                    dist_to_star = math.sqrt((pos_x - self.current_star_x)**2 + (pos_y - self.current_star_y)**2)
                    
                    # Só criar a partícula se estiver dentro do limite e maior que o mínimo
                    if 5 <= dist_to_star <= 100:  # Aumentado para 100px (era 40)
                        # Criar uma partícula extra nesta posição interpolada
                        tamanho = random.uniform(3.5, 5.5)  # Aumentado
                        
                        # Posição relativa ao canvas de partículas
                        rel_x = self.particles_center_x + (pos_x - self.current_star_x)
                        rel_y = self.particles_center_y + (pos_y - self.current_star_y)
                        
                        # Escolher uma cor aleatória para a partícula
                        cor = random.choice([
                            "#80B0FF",  # Azul claro original
                            "#60A0FF",  # Azul médio
                            "#4080FF",  # Azul mais intenso
                            "#A0D0FF",  # Azul muito claro
                            "#C0E0FF",  # Azul quase branco
                            "#FFFFFF"   # Branco puro
                        ])
                        
                        particula = {
                            "id": self.particles_canvas.create_oval(
                                rel_x - tamanho, rel_y - tamanho,
                                rel_x + tamanho, rel_y + tamanho,
                                fill=cor, outline="", stipple="gray12"
                            ),
                            "x": rel_x,
                            "y": rel_y,
                            "screen_x": pos_x,
                            "screen_y": pos_y,
                            "tamanho": tamanho,
                            "alpha": random.uniform(0.2, 0.4),  # Aumentada a opacidade inicial
                            "desvanecimento": random.uniform(0.03, 0.06),
                            "criacao": time.time(),
                            "cor": cor  # Guardar a cor da partícula
                        }
                        
                        self.trail_particles.append(particula)
        
        # Atualizar as partículas existentes
        for particula in self.trail_particles:
            try:
                # Calcular a idade da partícula
                idade = time.time() - particula["criacao"]
                
                # Calcular a distância da partícula até a posição atual da estrela
                dist_x = self.current_star_x - particula["screen_x"]
                dist_y = self.current_star_y - particula["screen_y"]
                distancia = math.sqrt(dist_x*dist_x + dist_y*dist_y)
                
                # Remover partículas velhas, muito próximas da estrela ou além da distância máxima
                if idade > self.vida_rastro or distancia > 100 or distancia < 5:  # Aumentado para 100px (era 40)
                    particulas_para_remover.append(particula)
                    self.particles_canvas.delete(particula["id"])
                    continue
                
                # Calcular fator de desvanecimento baseado na idade
                alpha_factor = 1.0 - (idade / self.vida_rastro)
                particula["alpha"] = max(0, alpha_factor * 0.4)  # Alpha máximo de 0.4
                
                # Redimensionar partícula com base na idade (encolher gradualmente)
                size_factor = 1.0 - (idade / self.vida_rastro * 0.3)  # Reduzido de 0.5 para 0.3 (encolhe menos)
                current_size = particula["tamanho"] * size_factor
                
                # Calcular a diferença entre a posição atual da janela e onde a partícula foi criada
                diff_x = self.current_star_x - particula["screen_x"]
                diff_y = self.current_star_y - particula["screen_y"]
                
                # Nova posição da partícula no canvas
                new_x = self.particles_center_x - diff_x
                new_y = self.particles_center_y - diff_y
                
                # Atualizar coordenadas da partícula
                self.particles_canvas.coords(
                    particula["id"],
                    new_x - current_size,
                    new_y - current_size,
                    new_x + current_size,
                    new_y + current_size
                )
                
                # Atualizar transparência
                stipple = ""
                if particula["alpha"] < 0.1:
                    stipple = "gray25"  # Menos transparente (era gray12)
                elif particula["alpha"] < 0.2:
                    stipple = "gray25"  # Menos transparente
                
                # Manter a cor original da partícula
                self.particles_canvas.itemconfig(particula["id"], fill=particula["cor"], stipple=stipple)
                
            except Exception as e:
                print(f"Erro ao atualizar partícula de rastro: {e}")
                particulas_para_remover.append(particula)
        
        # Remover as partículas marcadas
        for particula in particulas_para_remover:
            if particula in self.trail_particles:
                self.trail_particles.remove(particula)
    
    def criar_particula_brilho(self, tipo_rastro=False):
        """Cria uma pequena partícula brilhante ao redor da estrela"""
        try:
            # Tamanho pequeno e aleatório para as partículas
            tamanho = random.uniform(0.5, 1.5)
            
            # Gerar posição aleatória ao redor da estrela
            angulo = random.uniform(0, math.pi * 2)
            distancia = random.uniform(5, 10)  # Distância mínima de 5px do centro da estrela
            
            # Calcular posição relativa ao centro do canvas de partículas
            dx = math.cos(angulo) * distancia
            dy = math.sin(angulo) * distancia
            
            # Obter a posição atual do cursor
            cursor_x = self.root.winfo_pointerx()
            cursor_y = self.root.winfo_pointery()
            
            # Posição central no canvas de partículas - sempre usar o centro exato
            pos_x = self.particles_window_size // 2 + dx
            pos_y = self.particles_window_size // 2 + dy
            
            # Posição absoluta da partícula na tela
            abs_x = self.root.winfo_x() + (self.particles_window_size // 2) + dx
            abs_y = self.root.winfo_y() + (self.particles_window_size // 2) + dy
            
            # Verificar se a partícula estaria dentro da área do cursor
            part_to_cursor_dist = math.sqrt((abs_x - cursor_x)**2 + (abs_y - cursor_y)**2)
            
            # Se estiver muito perto do cursor, mudar a distância/ângulo para afastar
            if part_to_cursor_dist < self.min_distance:
                # Continuar tentando outra posição
                return
            
            # Obter cores baseadas na transição atual
            cores_atuais = self.obter_cores_atuais()
            
            # Cores possíveis para as partículas baseadas no estado atual de transição
            if tipo_rastro:
                # Para partículas de rastro
                if self.estado_cor_atual == "clique":
                    # Interpolação entre azul e violeta
                    cor_base_normal = random.choice(self.config['cores_rastro']['normal'])
                    cor_base_clique = random.choice(self.config['cores_rastro']['clique'])
                    r1, g1, b1 = int(cor_base_normal[1:3], 16), int(cor_base_normal[3:5], 16), int(cor_base_normal[5:7], 16)
                    r2, g2, b2 = int(cor_base_clique[1:3], 16), int(cor_base_clique[3:5], 16), int(cor_base_clique[5:7], 16)
                    r = int(r1 + (r2 - r1) * self.transicao_cor)
                    g = int(g1 + (g2 - g1) * self.transicao_cor)
                    b = int(b1 + (b2 - b1) * self.transicao_cor)
                    cor = f"#{r:02x}{g:02x}{b:02x}"
                elif self.estado_cor_atual == "digitacao":
                    # Interpolação entre azul e dourado
                    cor_base_normal = random.choice(self.config['cores_rastro']['normal'])
                    # Cores douradas para digitação
                    cor_base_digitacao = random.choice(["#FFD700", "#FFC125", "#FFB90F", "#FFA500", "#FF8C00"])
                    r1, g1, b1 = int(cor_base_normal[1:3], 16), int(cor_base_normal[3:5], 16), int(cor_base_normal[5:7], 16)
                    r2, g2, b2 = int(cor_base_digitacao[1:3], 16), int(cor_base_digitacao[3:5], 16), int(cor_base_digitacao[5:7], 16)
                    r = int(r1 + (r2 - r1) * self.transicao_cor)
                    g = int(g1 + (g2 - g1) * self.transicao_cor)
                    b = int(b1 + (b2 - b1) * self.transicao_cor)
                    cor = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    # Cores originais
                    cor = random.choice(self.config['cores_rastro']['normal'])
            else:
                # Para partículas estáticas
                if self.estado_cor_atual == "clique":
                    # Cores para partículas em modo clique
                    base_colors = ["#FFFFFF", "#E0A0FF", "#D280FF", "#C060FF", "#B040FF"]
                    cor_base_normal = random.choice(["#FFFFFF", "#E0F0FF", "#C0E0FF", "#A0C5FF", "#80B0FF"])
                    cor_base_clique = random.choice(base_colors)
                    r1, g1, b1 = int(cor_base_normal[1:3], 16), int(cor_base_normal[3:5], 16), int(cor_base_normal[5:7], 16)
                    r2, g2, b2 = int(cor_base_clique[1:3], 16), int(cor_base_clique[3:5], 16), int(cor_base_clique[5:7], 16)
                    r = int(r1 + (r2 - r1) * self.transicao_cor)
                    g = int(g1 + (g2 - g1) * self.transicao_cor)
                    b = int(b1 + (b2 - b1) * self.transicao_cor)
                    cor = f"#{r:02x}{g:02x}{b:02x}"
                elif self.estado_cor_atual == "digitacao":
                    # Cores para partículas em modo digitação
                    cor_base_normal = random.choice(["#FFFFFF", "#E0F0FF", "#C0E0FF", "#A0C5FF", "#80B0FF"])
                    cor_base_digitacao = random.choice(["#FFFFFF", "#FFFAF0", "#FFEC8B", "#FFD700", "#FFB90F"])
                    r1, g1, b1 = int(cor_base_normal[1:3], 16), int(cor_base_normal[3:5], 16), int(cor_base_normal[5:7], 16)
                    r2, g2, b2 = int(cor_base_digitacao[1:3], 16), int(cor_base_digitacao[3:5], 16), int(cor_base_digitacao[5:7], 16)
                    r = int(r1 + (r2 - r1) * self.transicao_cor)
                    g = int(g1 + (g2 - g1) * self.transicao_cor)
                    b = int(b1 + (b2 - b1) * self.transicao_cor)
                    cor = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    # Cores originais
                    cor = random.choice(["#FFFFFF", "#E0F0FF", "#C0E0FF", "#A0C5FF", "#80B0FF"])
            
            # Velocidade de movimento da partícula
            velocidade_x = random.uniform(-1.2, 1.2)  # Velocidade para efeito de emanação
            velocidade_y = random.uniform(-1.2, 1.2)
            
            # Criar a partícula no canvas das partículas
            id_particula = self.particles_canvas.create_oval(
                pos_x - tamanho,
                pos_y - tamanho,
                pos_x + tamanho,
                pos_y + tamanho,
                fill=cor, 
                outline="", 
                stipple="gray12"
            )
            
            # Definir o tipo da partícula (rastro ou estática)
            tipo = "rastro" if tipo_rastro else "estatica"
            
            # Adicionar à lista de partículas
            particula = {
                "id": id_particula,
                "tamanho": tamanho,
                "x": pos_x,  # Posição absoluta no canvas de partículas
                "y": pos_y,
                "screen_x": self.current_star_x,  # Posição absoluta da estrela na tela no momento da criação
                "screen_y": self.current_star_y,
                "offset_x": dx,  # Deslocamento relativo ao centro da estrela
                "offset_y": dy,
                "vel_x": velocidade_x,
                "vel_y": velocidade_y,
                "criacao": time.time(),
                "cor": cor,
                "alpha": 0.5,  # Iniciar com transparência
                "stipple": "gray12",
                "tipo": tipo  # Tipo de partícula: rastro ou estática
            }
            
            self.particulas_brilho.append(particula)
            
            # Limitar o número máximo de partículas
            if len(self.particulas_brilho) > self.max_particulas:
                # Remover a mais antiga
                antiga = self.particulas_brilho.pop(0)
                self.particles_canvas.delete(antiga["id"])
                
        except Exception as e:
            print(f"Erro ao criar partícula de brilho: {e}")
            
    def atualizar_particulas_brilho(self, dt):
        """Atualiza a posição e opacidade das partículas de brilho"""
        tempo_atual = time.time()
        remover = []
        
        # Obter a posição atual do cursor
        cursor_x = self.root.winfo_pointerx()
        cursor_y = self.root.winfo_pointery()
        
        for particula in self.particulas_brilho:
            try:
                # Calcular tempo de vida da partícula
                idade = tempo_atual - particula["criacao"]
                
                # Determinar o tempo de vida máximo com base no tipo de partícula
                vida_maxima = self.vida_brilho_rastro if particula["tipo"] == "rastro" else self.vida_brilho_estatico
                
                # Calcular a distância da partícula até a estrela atual
                dx = self.current_star_x - particula["screen_x"]
                dy = self.current_star_y - particula["screen_y"]
                distancia_da_estrela = math.sqrt(dx*dx + dy*dy)
                
                # Se a partícula estiver muito longe da estrela ou velha demais, marcá-la para remoção
                if distancia_da_estrela > 100 or idade >= vida_maxima:  # Aumentado para 100px (era 40)
                    remover.append(particula)
                    continue
                
                # Calcular fator de desvanecimento baseado na idade
                # Começa a desvanecer linearmente desde o início
                alpha = 1.0 - (idade / vida_maxima)
                particula["alpha"] = max(0, min(0.5, alpha * 0.5))  # Máximo de 0.5
                
                # Atualizar posição da partícula com sua velocidade - sempre se movendo para fora
                nova_x = particula["x"] + particula["vel_x"] * dt * 60
                nova_y = particula["y"] + particula["vel_y"] * dt * 60
                
                # Posição absoluta da partícula na tela
                abs_x = self.root.winfo_x() + nova_x
                abs_y = self.root.winfo_y() + nova_y
                
                # Verificar se a nova posição invadiria a área do cursor
                part_to_cursor_dist = math.sqrt((abs_x - cursor_x)**2 + (abs_y - cursor_y)**2)
                
                # Se estiver prestes a entrar na área do cursor, reverter a direção
                if part_to_cursor_dist < self.min_distance:
                    # Manter a posição atual e inverter a velocidade
                    particula["vel_x"] = -particula["vel_x"] * 1.2  # Aumentar um pouco a velocidade
                    particula["vel_y"] = -particula["vel_y"] * 1.2
                else:
                    # Atualizar a posição normalmente
                    particula["x"] = nova_x
                    particula["y"] = nova_y
                
                # Atualizar posição visual da partícula
                self.particles_canvas.coords(
                    particula["id"],
                    particula["x"] - particula["tamanho"],
                    particula["y"] - particula["tamanho"],
                    particula["x"] + particula["tamanho"],
                    particula["y"] + particula["tamanho"]
                )
                
                # Atualizar transparência baseada no alpha (muito mais transparente)
                if particula["alpha"] < 0.15:
                    stipple = "gray12"  # Quase invisível
                elif particula["alpha"] < 0.3:
                    stipple = "gray12"  # Quase invisível
                else:
                    stipple = "gray12"  # Quase invisível
                
                # Aplicar efeito de transparência
                self.particles_canvas.itemconfig(particula["id"], fill=particula["cor"], stipple=stipple)
                
            except Exception as e:
                print(f"Erro ao atualizar partícula de brilho: {e}")
                remover.append(particula)
        
        # Remover partículas marcadas
        for particula in remover:
            try:
                if particula in self.particulas_brilho:
                    self.particulas_brilho.remove(particula)
                self.particles_canvas.delete(particula["id"])
            except Exception as e:
                print(f"Erro ao remover partícula: {e}")
    
    def monitorar_mouse_teclado(self):
        """Monitora eventos globais de mouse e teclado usando win32api"""
        ultimo_estado_mouse = False
        ultimo_clique = time.time() - 10  # Iniciar como se o último clique fosse há 10 segundos
        
        # Lista para armazenar estados de teclas
        estados_teclas = {k: False for k in range(256)}  # Estado atual de todas as teclas
        
        while self.running:
            try:
                # Monitorar cliques de mouse usando win32api
                estado_mouse_atual = GetKeyState(0x01) < 0  # Botão esquerdo do mouse
                
                # Se o botão do mouse foi pressionado (transição de falso para verdadeiro)
                if estado_mouse_atual and not ultimo_estado_mouse:
                    tempo_atual = time.time()
                    if tempo_atual - ultimo_clique > 0.3:  # Reduzir debounce para 300ms
                        ultimo_clique = tempo_atual
                        # Acionar a função de clique diretamente
                        self.ativar_cor_clique()
                
                # Atualizar o último estado do mouse
                ultimo_estado_mouse = estado_mouse_atual
                
                # Verificar se alguma tecla está pressionada
                alguma_tecla_pressionada = False
                
                # Verificar teclas mais comuns primeiro (otimização)
                for i in range(65, 91):  # A-Z
                    estado_atual = GetKeyState(i) < 0
                    if estado_atual and not estados_teclas[i]:
                        alguma_tecla_pressionada = True
                        estados_teclas[i] = True
                        self.detectar_digitacao()
                        break
                    elif not estado_atual and estados_teclas[i]:
                        estados_teclas[i] = False
                
                # Se nenhuma letra foi pressionada, verificar números e outros
                if not alguma_tecla_pressionada:
                    for i in range(48, 58):  # 0-9
                        estado_atual = GetKeyState(i) < 0
                        if estado_atual and not estados_teclas[i]:
                            alguma_tecla_pressionada = True
                            estados_teclas[i] = True
                            self.detectar_digitacao()
                            break
                        elif not estado_atual and estados_teclas[i]:
                            estados_teclas[i] = False
                
                # Verificar teclas especiais (espaço, enter, backspace)
                teclas_especiais = [0x20, 0x0D, 0x08]  # Espaço, Enter, Backspace
                for i in teclas_especiais:
                    estado_atual = GetKeyState(i) < 0
                    if estado_atual and not estados_teclas[i]:
                        alguma_tecla_pressionada = True
                        estados_teclas[i] = True
                        self.detectar_digitacao()
                        break
                    elif not estado_atual and estados_teclas[i]:
                        estados_teclas[i] = False
                
                # Pausa para reduzir uso de CPU
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Erro ao monitorar mouse/teclado: {e}")
                time.sleep(0.1)  # Aguardar um pouco mais em caso de erro
    
    def detectar_digitacao(self, event=None):
        """Detecta quando o usuário está digitando"""
        try:
            self.tempo_ultima_digitacao = time.time()
            
            # Só muda para dourado se não estiver no modo clique
            if not self.cor_clique_ativa:
                self.cor_digitacao_ativa = True
                self.estado_cor_atual = "digitacao"
                
                # Iniciar transição de forma mais suave (25% em vez de 50%)
                if self.transicao_cor < 0.25:
                    self.transicao_cor = 0.25
                
                # Forçar atualização das cores
                self.update_animation(1/60)
        except Exception as e:
            print(f"Erro ao detectar digitação: {e}")

    def monitorar_inatividade(self):
        """Monitora o tempo de inatividade do usuário"""
        while self.running:
            tempo_atual = time.time()
            if self.cor_digitacao_ativa and (tempo_atual - self.tempo_ultima_digitacao) > self.tempo_inatividade:
                self.cor_digitacao_ativa = False
                self.estado_cor_atual = "normal"
            time.sleep(0.1)

    def quit(self, event=None):
        """Função para encerrar o programa"""
        self.running = False
        self.root.quit()

    def run(self):
        """Executa a aplicação"""
        try:
            # Registrar função para capturar tecla ESC
            self.root.bind("<Escape>", self.quit)
            self.particles_window.bind("<Escape>", self.quit)
            
            # Registrar função para capturar clique do mouse
            self.root.bind("<Button-1>", self.ativar_cor_clique)
            self.particles_window.bind("<Button-1>", self.ativar_cor_clique)
            
            # Posicionar a estrela inicialmente fora da tela
            self.current_star_x = -100
            self.current_star_y = -100
            
            # Iniciar o loop de atualização
            self.update(1/60)
            
            # Iniciar o loop principal
            self.root.mainloop()
            
        except Exception as e:
            print(f"Erro ao executar: {e}")
            
    def ativar_cor_clique(self, event=None):
        """Ativa a mudança de cor ao clicar no mouse"""
        self.cor_clique_ativa = True
        self.cor_digitacao_ativa = False  # Desativa a cor de digitação quando clicar
        self.tempo_inicio_clique = time.time()
        self.estado_cor_atual = "clique"
        
        # Iniciar com uma transição mais suave (25% em vez de 50%)
        if self.transicao_cor < 0.25:
            self.transicao_cor = 0.25
        
        # Forçar atualização imediata das cores
        self.update_animation(1/60)
            
    def update(self, dt):
        """Atualiza a posição da estrela e todos os efeitos visuais"""
        try:
            # Verificar e atualizar o estado da cor com base em eventos
            self.atualizar_cor_clique(dt)
            
            # Atualizar a posição da estrela (que já inclui a atualização da janela de partículas)
            self.follow_mouse(dt)
            
            # Atualizar a animação da estrela
            self.update_animation(dt)
            
            # Atualizar partículas e rastros
            self.atualizar_rastro(dt)
            self.atualizar_particulas_brilho(dt)
            
            # Criar novas partículas estáticas constantemente em cada frame
            # Sempre emanando luz, independente do movimento da estrela
            if random.random() < 0.8:  # 80% de chance por frame para criar efeito de emanação constante
                self.criar_particula_brilho(tipo_rastro=False)  # Criar partículas estáticas
                
            # Agendar próxima atualização
            self.root.after(int(1000/60), self.update, 1/60)  # Aproximadamente 60 FPS
            
        except Exception as e:
            print(f"Erro na atualização: {e}")
            # Em caso de erro, tentar continuar
            self.root.after(int(1000/60), self.update, 1/60)

    def animar_estrela_parada(self, cursor_x, cursor_y, dt):
        """Realizar animações especiais quando o mouse está parado"""
        try:
            # Tempo atual
            tempo_atual = time.time()
            delta_tempo = tempo_atual - self.ultimo_tempo_animacao
            self.ultimo_tempo_animacao = tempo_atual
            
            # Limitar delta_tempo para evitar saltos grandes caso o framerate caia
            delta_tempo = min(delta_tempo, 0.033)  # Máximo de ~30 FPS (era 0.05)
            
            # Incrementar o tempo da fase atual
            self.tempo_fase_animacao += delta_tempo
            
            # Variáveis para suavizar transições entre fases
            target_x = 0
            target_y = 0
            
            # Gerenciar a fase de animação
            if self.fase_animacao == 0:  # Rotação em volta do cursor
                # Aumentar o ângulo para movimento circular (velocidade gradual)
                self.angulo_animacao += self.velocidade_rotacao * delta_tempo * 0.7  # Reduzido para 70% da velocidade
                
                # Raio pulsante para efeito mais vivo (oscilação mais suave)
                raio_pulsante = self.raio_animacao + 8 * math.sin(self.angulo_animacao * 0.8)  # Oscilação mais lenta e menor
                
                # Calcular a posição alvo
                target_x = cursor_x + raio_pulsante * math.cos(self.angulo_animacao)
                target_y = cursor_y + raio_pulsante * math.sin(self.angulo_animacao)
                
                # Depois de 5 segundos, preparar para fase de aproximação
                if self.tempo_fase_animacao > 5.0:
                    # Guardar a posição atual para iniciar a transição suave
                    self.target_x_animacao = target_x
                    self.target_y_animacao = target_y
                    self.fase_animacao = 1
                    self.tempo_fase_animacao = 0
                    
            elif self.fase_animacao == 1:  # Aproximação ao cursor
                # Interpolar a posição entre o ponto atual da rotação e o cursor
                # Aumentar para 3 segundos para aproximação ainda mais suave
                progresso = min(1.0, self.tempo_fase_animacao / 3.0)  
                
                # Usar curva Cubic Bezier para um movimento extremamente suave
                # Aproximação mais gradual no início e fim
                t = progresso
                progresso = 3 * t * t - 2 * t * t * t  # Curva suave em S
                
                # Calcular posição alvo de forma mais suave
                target_x = self.target_x_animacao + (cursor_x - self.target_x_animacao) * progresso
                target_y = self.target_y_animacao + (cursor_y - self.target_y_animacao) * progresso
                
                # Depois de 3 segundos, preparar para fase de afastamento
                if self.tempo_fase_animacao > 3.0:
                    # Guardar posição atual como ponto de partida para próxima fase
                    self.fase_animacao = 2
                    self.tempo_fase_animacao = 0
                    # Manter referência de onde estamos atualmente
                    self.target_x_animacao = target_x
                    self.target_y_animacao = target_y
                    # Escolher ângulo de "fuga" aleatório, mas não muito diferente do atual
                    angulo_atual = math.atan2(target_y - cursor_y, target_x - cursor_x)
                    # Escolher ângulo próximo para evitar teleportes (variação máxima de 30°)
                    self.angulo_animacao = angulo_atual + random.uniform(-math.pi/6, math.pi/6)
                    
            elif self.fase_animacao == 2:  # Afastamento 
                # Calcular a posição alvo como um movimento para longe do cursor
                # Iniciar da distância atual para evitar saltos
                distancia_inicial = math.sqrt((self.target_x_animacao - cursor_x)**2 + (self.target_y_animacao - cursor_y)**2)
                
                # Usar função exponencial suave para aceleração gradual
                progresso = 1.0 - math.exp(-2.0 * self.tempo_fase_animacao)  # Função exponencial mais suave
                distancia = distancia_inicial + 80 * progresso  # Distância máxima menor e mais controlada
                
                # Adicionar oscilação ao ângulo para movimento errático muito leve
                self.angulo_animacao += math.sin(self.tempo_fase_animacao * 4) * 0.03  # Oscilação extremamente pequena
                
                # Calcular posição alvo
                target_x = cursor_x + distancia * math.cos(self.angulo_animacao)
                target_y = cursor_y + distancia * math.sin(self.angulo_animacao)
                
                # Depois de 2 segundos, preparar para fase de dança
                if self.tempo_fase_animacao > 2.0:
                    self.fase_animacao = 3
                    self.tempo_fase_animacao = 0
                    self.raio_animacao = distancia  # Usar a distância atual como raio
                    # Manter referência da posição atual
                    self.target_x_animacao = target_x
                    self.target_y_animacao = target_y
                    
            elif self.fase_animacao == 3:  # Dança final
                # Movimento em formato de "8" ou dança (lemniscata)
                t = self.tempo_fase_animacao
                
                # Velocidade constante para movimento mais previsível e suave
                angulo = t * 0.8  # Velocidade reduzida e constante
                
                # Calcular centro do movimento baseado na posição do cursor com offset fixo
                centro_x = cursor_x + 60 * math.cos(self.angulo_animacao)
                centro_y = cursor_y + 60 * math.sin(self.angulo_animacao)
                
                # Parametrização de curva em formato de 8 (suave)
                # Usar amplitude fixa para evitar oscilações
                scale_x = 40
                scale_y = 25  # Menor amplitude vertical para dança mais controlada
                
                # Calcular posição com funções trigonométricas para suavidade máxima
                target_x = centro_x + scale_x * math.sin(angulo)
                target_y = centro_y + scale_y * math.sin(angulo * 2)
                
                # Fazer transição suave do início da dança com 1 segundo completo
                if self.tempo_fase_animacao < 1.0:
                    # No primeiro segundo, fazer interpolação da posição anterior para a dança
                    progresso = self.tempo_fase_animacao
                    
                    # Função de suavização cúbica para transição perfeita
                    suavizacao = progresso * progresso * (3 - 2 * progresso)
                    
                    # Interpolar da posição anterior para a atual
                    target_x = self.target_x_animacao + (target_x - self.target_x_animacao) * suavizacao
                    target_y = self.target_y_animacao + (target_y - self.target_y_animacao) * suavizacao
                
                # Depois de 4 segundos, preparar transição de volta à rotação
                if self.tempo_fase_animacao > 4.0:
                    # Guardar posição atual para transição suave
                    self.target_x_animacao = target_x
                    self.target_y_animacao = target_y
                    
                    # Calcular ângulo atual em relação ao cursor para iniciar rotação sem pulos
                    self.angulo_animacao = math.atan2(target_y - cursor_y, target_x - cursor_x)
                    
                    self.fase_animacao = 0
                    self.tempo_fase_animacao = 0
                    # Usar a distância atual como raio inicial da rotação
                    self.raio_animacao = math.sqrt((target_x - cursor_x)**2 + (target_y - cursor_y)**2)
                    self.velocidade_rotacao = 1.7  # Velocidade fixa para previsibilidade
            
            # Adicionar movimento aleatório extremamente pequeno, quase imperceptível
            pequeno_ajuste_x = random.uniform(-0.5, 0.5)  # Foi reduzido de -1.5/1.5 para -0.5/0.5
            pequeno_ajuste_y = random.uniform(-0.5, 0.5)
            target_x += pequeno_ajuste_x
            target_y += pequeno_ajuste_y
            
            # Aplicar limitação na variação de posição entre frames para evitar qualquer teleporte
            if hasattr(self, 'last_target_x') and hasattr(self, 'last_target_y'):
                dx = target_x - self.last_target_x
                dy = target_y - self.last_target_y
                distancia = math.sqrt(dx*dx + dy*dy)
                
                # Se a distância for grande demais, limitar o movimento ainda mais
                max_deslocamento = 3.0  # Reduzido de 5.0 para 3.0 para movimento ultra-suave
                if distancia > max_deslocamento:
                    fator = max_deslocamento / distancia
                    target_x = self.last_target_x + dx * fator
                    target_y = self.last_target_y + dy * fator
            
            # Armazenar última posição alvo para o próximo frame
            self.last_target_x = target_x
            self.last_target_y = target_y
            
            return target_x, target_y
            
        except Exception as e:
            # Em caso de erro, retornar a última posição conhecida em vez de teleportar
            if hasattr(self, 'last_target_x') and hasattr(self, 'last_target_y'):
                return self.last_target_x, self.last_target_y
            else:
                return cursor_x + 80, cursor_y

def main():
    """Função principal que inicia a aplicação"""
    try:
        app = MouseFollower()
        app.run()
    except Exception as e:
        print(f"Erro na inicialização: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True

if __name__ == "__main__":
    # Iniciar a aplicação
    sys.exit(0 if main() else 1)
