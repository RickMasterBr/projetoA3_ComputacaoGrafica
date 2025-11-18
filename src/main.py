import glfw
from OpenGL.GL import *
import settings # As constantes
from shader import Shader # Importar a classe Shader
import glm # Biblioteca para manipulação de vetores e matrizes
from camera import Camera # Importar a classe Camera
from terrain import Terrain # Importar a classe Terrain
from shadow_mapper import ShadowMapper # Importar a classe ShadowMapper
from model import Model # Importar a classe Model

class Engine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Inicializar o glfw
        if not glfw.init():
            raise Exception("GLFW não pôde ser inicializado.")
        
        # Configurar a Janela com OpenGl Moderno
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1) #OpenGL 4.1
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE) # macOS
        
        # Criar a Janela
        self.window = glfw.create_window(self.width, self.height, "Projeto A3 - OpenGL", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("A janela não pôde ser criada")
        
        # Tornar o contexto da janela o principal
        glfw.make_context_current(self.window)

        # Habilitar o Teste de Profundidade
        glEnable(GL_DEPTH_TEST)

        # Variaveis para o delta_time ( tempo entre frames )
        self.last_time = glfw.get_time()
        self.delta_time = 0.0

        # Instanciar a câmera
        self.camera = Camera(position=glm.vec3(0,5,0)) # Posição inicial da câmera

        # Logica do Mouse
        self.last_mouse_x = self.width / 2
        self.last_mouse_y = self.height / 2
        self.first_mouse = True

        # Capturar o cursor e registrar o callback
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED) 
        glfw.set_cursor_pos_callback(self.window, self.mouse_callback) 

        # Variáveis de Cena para o ciclo do dia
        self.scene_time = 0.0 # Tempo em segundos desde o início do programa
        self.sun_direction = glm.vec3(1.0, 0.0, 0.0) # Direção inicial do sol
        self.ski_color = settings.COLOR_DAY # Cor inicial do céu


        # Testar o carregamento do shader
        try:
            self.terrain_shader = Shader("shaders/terrain.vert", "shaders/terrain.frag")
            self.shadow_shader = Shader("shaders/shadow_map.vert", "shaders/shadow_map.frag")

            # NOVO SHADER DE PERSONAGEM
            self.model_shader = Shader("shaders/animated_model.vert", "shaders/animated_model.frag")

            # Inicializar o terreno com o shader
            self.terrain = Terrain(self.terrain_shader)

            # NOVO PERSONAGEM
            self.character = Model("assets/models/character.fbx", self.model_shader)

            self.shadow_mapper = ShadowMapper()

        except Exception as e:
            print(f"Falha ao inicializar o shader: {e}")
            glfw.terminate()
            exit() # Sair se os shaders não carregarem

    def run(self):
        
        # Implementar o Loop (Manter o programa rodando)
        while not glfw.window_should_close(self.window):
            
            # Calcular o delta_time ( deve ser o primeiro passo do loop )
            current_time = glfw.get_time()
            self.delta_time = current_time - self.last_time
            self.last_time = current_time

            # Verificar eventos (Como fechar a janela)
            glfw.poll_events()

            self.process_keyboard_input()

            # Atualizar a física da câmera
            self.camera.update_physics(self.delta_time, self.terrain)

            # Atualizar o ciclo do dia
            self.update_day_night_cycle()

            # Renderizar a sombras
            # Pegar a altura do terreno no centro para posicionar o personagem
            terrain_height_at_center = self.terrain.get_height(0, 0)

            # Renderizar o mapa de sombras
            # Calcular a Matriz de Luz (Câmera do Sol)
            # Projeção Ortográfica (Sol é luz direcional, raios paralelos)
            # Abrange uma área de 100x100 ao redor da câmera
            near_plane = 1.0
            far_plane = 200.0
            size = 80.0 
            light_projection = glm.ortho(-size, size, -size, size, near_plane, far_plane)
            
            # Visão: O sol olha para a posição da câmera do jogador (mas de longe)
            # Posicionamos o "olho" do sol na direção da luz, a 100m de distância
            light_pos = self.camera.pos + (self.sun_direction * 100.0)
            light_view = glm.lookAt(light_pos, self.camera.pos, glm.vec3(0, 1, 0))
            
            light_space_matrix = light_projection * light_view

            # Renderizar
            self.shadow_mapper.bind() # Ativa o framebuffer de sombra
            
            # Usar o shader simples de sombra
            self.shadow_shader.use()
            self.shadow_shader.set_uniform_mat4("lightSpaceMatrix", light_space_matrix)
            
            # Desenhar o terreno (apenas geometria) para o mapa de sombra
            # Precisamos de um método draw simples no terrain ou passar o shader de sombra
            # TRUQUE: Vamos adicionar um 'override_shader' no draw do Terrain
            self.terrain.draw(self.camera, projection=None, sun_direction=None, override_shader=self.shadow_shader)
            
            # Desenha Personagem na Sombra
            model_matrix = glm.translate(glm.mat4(1.0), glm.vec3(0, terrain_height_at_center, 0))
            # Reduzir escala se o boneco for gigante (comum no Mixamo)
            model_matrix = glm.scale(model_matrix, glm.vec3(0.01, 0.01, 0.01)) 
            
            self.shadow_shader.set_uniform_mat4("model", model_matrix)
            self.character.draw(self.shadow_shader) # Usa o shader de sombra

            self.shadow_mapper.unbind(self.width, self.height) # Volta pra tela normal

            # RENDERIZAR CENA NORMAL (Com Sombras)
            # definir a cor do céu baseado na hora do dia
            glClearColor(self.sky_color.r, self.sky_color.g, self.sky_color.b, 1.0)

            # limpar a tela antes de desenhar um novo quadro
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Renderizar o Terreno
            # Cria a matriz de projeção (Lente da câmera)
            projection = glm.perspective(glm.radians(45.0), self.width / self.height, 0.1, 1000.0)
            
            # Configurar Shader do Terreno para receber sombras
            self.terrain_shader.use()
            self.terrain_shader.set_uniform_mat4("u_light_space_matrix", light_space_matrix) # <--- Envia a matriz
            self.terrain_shader.set_uniform_int("u_shadow_map", 1) # <--- Textura na unidade 1
            
            # Ativar a textura de sombra na unidade 1
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.shadow_mapper.depth_map_texture)

            # Desenhar o terreno considerando a direção do sol
            self.terrain.draw(self.camera, projection, self.sun_direction)

            # Desenha o Personagem 
            self.model_shader.use()
            self.model_shader.set_uniform_mat4("view", self.camera.get_view_matrix())
            self.model_shader.set_uniform_mat4("projection", projection)
            self.model_shader.set_uniform_vec3("u_sun_direction", self.sun_direction)
            self.model_shader.set_uniform_vec3("u_sun_color", settings.COLOR_SUN)
            self.model_shader.set_uniform_vec3("u_ambient_color", settings.COLOR_AMBIENT)
            self.model_shader.set_uniform_mat4("u_light_space_matrix", light_space_matrix)
            self.model_shader.set_uniform_int("u_shadow_map", 1) # Mesma textura de sombra

            # Matriz de Modelo (Mesma da sombra)
            # Vamos pegar a altura do terreno no centro (0,0) para ele não afundar
            h = self.terrain.get_height(0, 0)
            model_matrix = glm.translate(glm.mat4(1.0), glm.vec3(0, h, 0))
            model_matrix = glm.scale(model_matrix, glm.vec3(0.01, 0.01, 0.01)) # Ajuste a escala conforme necessário (0.01 é um chute seguro para FBX)
            
            self.model_shader.set_uniform_mat4("model", model_matrix)
            
            # Ativar textura de sombra (já deve estar ativa do terreno, mas garante)
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.shadow_mapper.depth_map_texture)

            self.character.draw(self.model_shader)

            # Mostrar o que foi desenhado
            glfw.swap_buffers(self.window)
            
        #Finalizar
        glfw.terminate()

    def mouse_callback(self, window, xpos, ypos):
        """Callback do movimento do mouse"""

        if self.first_mouse:
            self.last_mouse_x = xpos
            self.last_mouse_y = ypos
            self.first_mouse = False

        x_offset = xpos - self.last_mouse_x
        y_offset = self.last_mouse_y - ypos # Invertido (Y cresce para baixo)

        self.last_mouse_x = xpos
        self.last_mouse_y = ypos

        self.camera.process_mouse_movement(x_offset, y_offset)

    def process_keyboard_input(self):
        """Processa o input do teclado (Seção III, Regra 4)."""
        
        # Fechar com ESC
        if glfw.get_key(self.window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(self.window, True)


        # Lógica de Movimento
        
        # Correndo
        multiplier = 1.0
        if glfw.get_key(self.window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS: #
            multiplier = settings.CAMERA_RUN_MULTIPLIER #

        velocity = settings.CAMERA_SPEED * multiplier * self.delta_time

        # Cria um vetor que impede que "olhar para cima" faça a camera voar
        front_xz = glm.normalize(glm.vec3(self.camera.front.x, 0.0, self.camera.front.z))

        # Vetor para A/D
        right_vector = glm.normalize(glm.cross(self.camera.front, self.camera.up))

        # Andar (W/S) e (A/D)
        if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS: #
            self.camera.pos += front_xz * velocity #
        if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
            self.camera.pos -= front_xz * velocity

        right_vector = glm.normalize(glm.cross(self.camera.front, self.camera.up)) #
        if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS: #
            self.camera.pos -= right_vector * velocity #
        if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
            self.camera.pos += right_vector * velocity

        # Pular (Barra de Espaço)
        if glfw.get_key(self.window, glfw.KEY_SPACE) == glfw.PRESS:
            self.camera.jump()
        
    def update_day_night_cycle(self):
        """Calcula a posição do sol e a cor do ceú"""

        # Simulação do Sol, o projeto pede 1 min real = 1 hora no jogo (ou seja, 60x mais rápido)
        # (Vamos usar 20x mais rápido para testar, senão é muito lento)
        self.scene_time += self.delta_time * 20.0 
        
        # game_hour = (self.scene_time / 60.0) % 24.0 # (Fórmula do PDF)
        game_hour = (self.scene_time / 5.0) % 24.0 # (Mais rápido para teste)

        # Converter hora em ângulo (0-24h -> 0-2PI)
        angle = (game_hour / 24.0) * 2.0 * glm.pi()

        # Ajustar o ângulo para o sol nascer no Leste (X+) e se pôr no Oeste (X-)
        # Para começar no Leste (X+), precisamos de um offset de -PI/2 (ou 18h)
        start_angle = angle - (glm.pi() / 2.0)
        self.sun_direction = glm.normalize(glm.vec3(glm.cos(start_angle), glm.sin(start_angle), 0.1))

        # Céu Dinâmico
        sun_height = self.sun_direction.y # Altura do sol (-1 a +1)
        
        # Lógica de interpolação
        if sun_height > 0.1: # Dia
            # Interpola do Pôr do Sol (0.1) para o Meio-Dia (1.0)
            factor = (sun_height - 0.1) / 0.9
            self.sky_color = glm.lerp(settings.COLOR_SUNSET, settings.COLOR_DAY, factor)
        elif sun_height > -0.1: # Pôr/Nascer do sol
            # Interpola da Noite (-0.1) para o Pôr do Sol (0.1)
            factor = (sun_height + 0.1) / 0.2
            self.sky_color = glm.lerp(settings.COLOR_NIGHT, settings.COLOR_SUNSET, factor)
        else: # Noite
            self.sky_color = settings.COLOR_NIGHT

if __name__ == "__main__":
    # Iniciar a aplicação
    engine = Engine(settings.WIN_WIDTH, settings.WIN_HEIGHT)
    print("Aplicação iniciada. Executando...")
    engine.run()
    print("Aplicação Finalizada.")