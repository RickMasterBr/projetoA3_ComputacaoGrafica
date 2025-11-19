import glfw
from OpenGL.GL import *
import settings # As constantes
from shader import Shader # Importar a classe Shader
import glm # Biblioteca para manipulação de vetores e matrizes
from camera import Camera # Importar a classe Camera
from terrain import Terrain # Importar a classe Terrain
from shadow_mapper import ShadowMapper # Importar a classe ShadowMapper
from model import Model # Importar a classe Model
from text_renderer import TextRenderer

import numpy as np



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
        
        self.sun_direction = glm.normalize(glm.vec3(0.3, 0.6, 0.2))

        # ----------- SHADER DO SOL -----------
        self.sun_shader = Shader("shaders/sun.vert", "shaders/sun.frag")

        # Quad de 2 triângulos
        sun_vertices = np.array([
            -1.0, -1.0, 0.0,
             1.0, -1.0, 0.0,
             1.0,  1.0, 0.0,
            -1.0,  1.0, 0.0
        ], dtype=np.float32)

        sun_indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        self.sun_vao = glGenVertexArrays(1)
        self.sun_vbo = glGenBuffers(1)
        self.sun_ebo = glGenBuffers(1)

        glBindVertexArray(self.sun_vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.sun_vbo)
        glBufferData(GL_ARRAY_BUFFER, sun_vertices.nbytes, sun_vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.sun_ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, sun_indices.nbytes, sun_indices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))

        glBindVertexArray(0)



        # Instanciar a câmera
        self.camera = Camera(position=glm.vec3(0,5,0)) # Posição inicial da câmera

        # Logica do Mouse
        self.last_mouse_x = self.width / 2
        self.last_mouse_y = self.height / 2
        self.first_mouse = True

        # Capturar o cursor e registrar o callback
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED) 
        glfw.set_cursor_pos_callback(self.window, self.mouse_callback) 

        self.terrain_height_at_center = 0.0
        

        # Variáveis de Cena para o ciclo do dia
        self.scene_time = 0.0 # Tempo em segundos desde o início do programa
        self.sun_direction = glm.vec3(1.0, 0.0, 0.0) # Direção inicial do sol
        self.ski_color = settings.COLOR_DAY # Cor inicial do céu

        # Relogio 
        self.text_shader = Shader("shaders/text.vert", "shaders/text.frag")
        self.text_renderer = TextRenderer("assets/fonts/OpenSansHebrew-Regular.ttf", 32)

        # Projeção ortográfica para HUD do relogio
        self.hud_projection = glm.ortho(0, self.width, 0, self.height)



        # Testar o carregamento do shader
        try:
            self.terrain_shader = Shader("shaders/terrain.vert", "shaders/terrain.frag")
            self.shadow_shader = Shader("shaders/shadow_map.vert", "shaders/shadow_map.frag")

            # NOVO SHADER DE PERSONAGEM
            self.model_shader = Shader("shaders/animated_model.vert", "shaders/animated_model.frag")

            # Inicializar o terreno com o shader
            self.terrain = Terrain(self.terrain_shader)

            # NOVO PERSONAGEM
            self.character = Model("assets/models/character.glb", self.model_shader)

            self.shadow_mapper = ShadowMapper()

        except Exception as e:
            print(f"Falha ao inicializar o shader: {e}")
            glfw.terminate()
            exit() # Sair se os shaders não carregarem

    def run(self):
    # Loop principal
     while not glfw.window_should_close(self.window):
        # ---------- tempo ----------
        current_time = glfw.get_time()
        self.delta_time = current_time - self.last_time
        self.last_time = current_time

        # ---------- eventos e input ----------
        glfw.poll_events()
        self.process_keyboard_input()

        # ---------- física da câmera ----------
        self.camera.update_physics(self.delta_time, self.terrain)

        # ---------- atualizar ciclo dia/noite ----------
        self.update_day_night_cycle()

        # ---------- preparar dados para sombras ----------
        # pegar altura do terreno para posicionamento
        self.terrain_height_at_center = self.terrain.get_height(0, 0)

        # matriz ortográfica para luz direcional (sol)
        near_plane = 1.0
        far_plane = 200.0
        size = 80.0
        light_projection = glm.ortho(-size, size, -size, size, near_plane, far_plane)

        # posição "olho" do sol a certa distância na direção da luz
        light_pos = self.camera.pos + (self.sun_direction * 100.0)
        light_view = glm.lookAt(light_pos, self.camera.pos, glm.vec3(0, 1, 0))
        light_space_matrix = light_projection * light_view

        # ---------- gerar mapa de sombras (depth map) ----------
        self.shadow_mapper.bind()
        self.shadow_shader.use()
        self.shadow_shader.set_uniform_mat4("lightSpaceMatrix", light_space_matrix)

        # desenhar apenas geometria para o depth map (override shader)
        # supondo que terrain.draw aceita override_shader (como você comentou)
        self.terrain.draw(self.camera, projection=None, sun_direction=None, override_shader=self.shadow_shader)

        # desenhar o personagem no mapa de sombra
        model_matrix = glm.translate(glm.mat4(1.0), glm.vec3(0, self.terrain_height_at_center, 0))
        model_matrix = glm.scale(model_matrix, glm.vec3(0.01, 0.01, 0.01))
        self.shadow_shader.set_uniform_mat4("model", model_matrix)
        self.character.draw(self.shadow_shader)

        self.shadow_mapper.unbind(self.width, self.height)

        # ---------- limpar framebuffer principal e configurar céu ----------
        glClearColor(self.sky_color.r, self.sky_color.g, self.sky_color.b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # ---------- projeção principal ----------
        projection = glm.perspective(glm.radians(45.0), self.width / self.height, 0.1, 1000.0)

        # ---------- desenhar terreno (com sombras) ----------
        self.terrain_shader.use()
        self.terrain_shader.set_uniform_mat4("u_light_space_matrix", light_space_matrix)
        self.terrain_shader.set_uniform_int("u_shadow_map", 1)  # textura na unidade 1

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_mapper.depth_map_texture)

        self.terrain.draw(self.camera, projection, self.sun_direction)

        # ---------- desenhar personagem (com sombras e iluminação) ----------
        self.model_shader.use()
        self.model_shader.set_uniform_mat4("view", self.camera.get_view_matrix())
        self.model_shader.set_uniform_mat4("projection", projection)
        self.model_shader.set_uniform_vec3("u_sun_direction", self.sun_direction)
        self.model_shader.set_uniform_vec3("u_sun_color", settings.COLOR_SUN)
        self.model_shader.set_uniform_vec3("u_ambient_color", settings.COLOR_AMBIENT)
        self.model_shader.set_uniform_mat4("u_light_space_matrix", light_space_matrix)
        self.model_shader.set_uniform_int("u_shadow_map", 1)

        escala = 4.0
        model_matrix = glm.translate(glm.mat4(1.0), glm.vec3(0, self.terrain_height_at_center, 0))
        model_matrix = glm.scale(model_matrix, glm.vec3(escala, escala, escala))

        self.character.update_animation(self.delta_time)
        self.model_shader.set_uniform_mat4("model", model_matrix)

        # garantir que a textura de sombra está ativa
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_mapper.depth_map_texture)

        self.character.draw(self.model_shader)

        # ---------- desenhar o sol (BILLBOARD) -----------
        # chama seu método render_sun, que espera a projection principal
        self.render_sun(projection)

        # ---------- HUD (relógio) ----------
        game_hour = (self.scene_time / 60.0) % 24.0
        hour = int(game_hour)
        minute = int((game_hour - hour) * 60)
        time_str = f"{hour:02d}:{minute:02d}"

        # HUD sempre por cima
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.text_shader.use()
        self.text_shader.set_uniform_mat4("projection", self.hud_projection)
        self.text_shader.set_uniform_int("text", 0)

        self.text_renderer.render_text(
            self.text_shader,
            time_str,
            20,
            self.height - 40,
            1.0,
            (1.0, 1.0, 1.0)
        )

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

        # ---------- trocar buffers ----------
        glfw.swap_buffers(self.window)

    # finalizar
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
        
        
        
        
        
    def render_sun(self, projection):
        self.sun_shader.use()

        # posição do sol a 200 metros na direção dele
        sun_pos_world = self.camera.pos + self.sun_direction * 200.0

        view = self.camera.get_view_matrix()

        # Billboard = remove rotação da view
        billboard_view = glm.mat4(glm.mat3(view))

        # Model = traduz para posição do sol, escalar um pouco
        model = glm.translate(glm.mat4(1.0), sun_pos_world)
        model = model * glm.inverse(billboard_view)   # faz o quad ficar sempre virado pra câmera
        model = glm.scale(model, glm.vec3(10.0, 10.0, 10.0))  # tamanho do sol

        self.sun_shader.set_uniform_mat4("projection", projection)
        self.sun_shader.set_uniform_mat4("view", view)
        self.sun_shader.set_uniform_mat4("model", model)

        # desenhar quad
        glDisable(GL_DEPTH_TEST)   # evita o sol ficar "cortado" pelo terreno
        glBindVertexArray(self.sun_vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glEnable(GL_DEPTH_TEST)
        
        
        
    def update_day_night_cycle(self):
        """Calcula a posição do sol e a cor do ceú"""

        # Simulação do Sol, o projeto pede 1 min real = 1 hora no jogo (ou seja, 60x mais rápido)
        # (Vamos usar 20x mais rápido para testar, senão é muito lento)
        # deixei mais lenta -- jorge
        self.scene_time += self.delta_time * 2
        
        # game_hour = (self.scene_time / 60.0) % 24.0 # (Fórmula do PDF)
        game_hour = (self.scene_time / 60.0) % 24.0 # (Mais rápido para teste)

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