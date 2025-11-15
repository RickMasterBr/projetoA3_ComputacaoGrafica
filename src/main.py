import glfw
from OpenGL.GL import *
import settings # As constantes
from shader import Shader # Importar a classe Shader
import glm # Biblioteca para manipulação de vetores e matrizes
from camera import Camera # Importar a classe Camera
from terrain import Terrain # Importar a classe Terrain

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


        # Testar o carregamento do shader
        try:
            self.terrain_shader = Shader("shaders/terrain.vert", "shaders/terrain.frag")
            # Inicializar o terreno
            self.terrain = Terrain(self.terrain_shader)
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
            
            # Definir a cor do mundo (Azul)
            glClearColor(0.1, 0.4, 0.7, 1.0)

            # limpar a tela antes de desenhar um novo quadro
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Renderizar o Terreno
            # Cria a matriz de projeção (Lente da câmera)
            projection = glm.perspective(glm.radians(45.0), self.width / self.height, 0.1, 1000.0)
            
            # Desenhar o terreno
            self.terrain.draw(self.camera, projection)

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

        # 6. Lógica de Movimento
        
        # Correndo
        multiplier = 1.0
        if glfw.get_key(self.window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS: #
            multiplier = settings.CAMERA_RUN_MULTIPLIER #

        velocity = settings.CAMERA_SPEED * multiplier * self.delta_time

        # Andar (W/S)
        if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS: #
            self.camera.pos += self.camera.front * velocity #
        if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
            self.camera.pos -= self.camera.front * velocity

        # Andar (A/D)
        right_vector = glm.normalize(glm.cross(self.camera.front, self.camera.up)) #
        if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS: #
            self.camera.pos -= right_vector * velocity #
        if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
            self.camera.pos += right_vector * velocity
        
if __name__ == "__main__":
    # Iniciar a aplicação
    engine = Engine(settings.WIN_WIDTH, settings.WIN_HEIGHT)
    print("Aplicação iniciada. Executando...")
    engine.run()
    print("Aplicação Finalizada.")