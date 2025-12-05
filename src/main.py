import glfw
from OpenGL.GL import *
import settings 
from shader import Shader 
import glm 
from camera import Camera 
from terrain import Terrain 
from shadow_mapper import ShadowMapper 
from model import Model 
from text_renderer import TextRenderer
from vegetation import Vegetation
from population import Population
from water import Water
import math
import numpy as np

class Engine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        if not glfw.init():
            raise Exception("GLFW não pôde ser inicializado.")
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1) 
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE) 
        
        self.window = glfw.create_window(self.width, self.height, "Projeto A3 - OpenGL", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("A janela não pôde ser criada")
        
        glfw.make_context_current(self.window)
        glEnable(GL_DEPTH_TEST)

        self.last_time = glfw.get_time()
        self.delta_time = 0.0

        # ----------- SHADER DO SOL -----------
        self.sun_shader = Shader("shaders/sun.vert", "shaders/sun.frag")

        sun_vertices = np.array([
            -1.0, -1.0, 0.0, 1.0, -1.0, 0.0, 1.0, 1.0, 0.0, -1.0, 1.0, 0.0
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

        self.camera = Camera(position=glm.vec3(0,5,0)) 
        self.last_mouse_x = self.width / 2
        self.last_mouse_y = self.height / 2
        self.first_mouse = True

        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED) 
        glfw.set_cursor_pos_callback(self.window, self.mouse_callback) 

        self.terrain_height_at_center = 0.0
        
        self.scene_time = 480.0 
        self.sun_direction = glm.vec3(1.0, 0.0, 0.0) 
        self.sky_color = settings.COLOR_DAY 

        self.outline_shader = Shader("shaders/outline.vert", "shaders/outline.frag")
        self.text_shader = Shader("shaders/text.vert", "shaders/text.frag")
        self.text_renderer = TextRenderer("assets/fonts/OpenSansHebrew-Regular.ttf", 32)
        self.hud_projection = glm.ortho(0, self.width, 0, self.height)

        try:
            self.terrain_shader = Shader("shaders/terrain.vert", "shaders/terrain.frag")
            self.shadow_shader = Shader("shaders/shadow_map.vert", "shaders/shadow_map.frag")
            self.model_shader = Shader("shaders/animated_model.vert", "shaders/animated_model.frag")

            self.terrain = Terrain(self.terrain_shader)
            self.vegetation = Vegetation(self.terrain, count=200)

            self.character = Model("assets/models/character.glb", self.model_shader)
            self.abe = Model("assets/models/abe.glb", self.model_shader)
            self.boss = Model("assets/models/boss.glb", self.model_shader)
            self.michelle = Model("assets/models/michelle.glb", self.model_shader)

            models_list = [self.character, self.abe, self.boss, self.michelle]
            self.population = Population(self.terrain, models_list, count=80)
            
            self.water = Water(size=800, height=12.0)
            self.shadow_mapper = ShadowMapper()

        except Exception as e:
            print(f"Falha ao inicializar o shader: {e}")
            glfw.terminate()
            exit()

    def render_with_outline(self, model_obj, view, projection, model_matrix=None, thickness=0.12):
        glCullFace(GL_FRONT) 
        self.outline_shader.use()
        self.outline_shader.set_uniform_mat4("view", view)
        self.outline_shader.set_uniform_mat4("projection", projection)
        self.outline_shader.set_uniform_float("u_thickness", thickness) 
        
        if model_matrix is None:
             self.outline_shader.set_uniform_mat4("model", glm.mat4(1.0))
        else:
             self.outline_shader.set_uniform_mat4("model", model_matrix)

        if isinstance(model_obj, Terrain):
             model_obj.draw(None, None, None, override_shader=self.outline_shader)
        elif isinstance(model_obj, Vegetation):
             glBindVertexArray(model_obj.vao)
             vertex_count = len(model_obj.vertices) // 9 
             glDrawArrays(GL_TRIANGLES, 0, vertex_count)
             glBindVertexArray(0)
        else:
             model_obj.draw(self.outline_shader)
        glCullFace(GL_BACK)

    def run(self):
        while not glfw.window_should_close(self.window):
            # ---------- Tempo ----------
            current_time = glfw.get_time()
            self.delta_time = current_time - self.last_time
            self.last_time = current_time

            # ---------- Input ----------
            glfw.poll_events()
            self.process_keyboard_input()
            self.camera.update_physics(self.delta_time, self.terrain, self.vegetation)
            self.update_day_night_cycle()

            # ---------- PASSO 1: MAPA DE SOMBRAS (Onde a mágica acontece) ----------
            
            self.terrain_height_at_center = self.terrain.get_height(0, 0)

            # Matriz ortográfica para luz direcional (Sol)
            # Aumentei o range (size 150) para cobrir mais da ilha
            near_plane = 1.0
            far_plane = 300.0
            size = 150.0 
            light_projection = glm.ortho(-size, size, -size, size, near_plane, far_plane)

            # O sol olha para onde o jogador está
            light_pos = self.camera.pos + (self.sun_direction * 150.0)
            light_view = glm.lookAt(light_pos, self.camera.pos, glm.vec3(0, 1, 0))
            light_space_matrix = light_projection * light_view

            # Ativar Framebuffer de Sombra
            self.shadow_mapper.bind()
            
            # Usar shader de sombra
            self.shadow_shader.use()
            self.shadow_shader.set_uniform_mat4("lightSpaceMatrix", light_space_matrix)

            # 1. Desenhar Terreno na Sombra
            self.terrain.draw(self.camera, projection=None, sun_direction=None, override_shader=self.shadow_shader)

            # 2. Desenhar Vegetação na Sombra (Aqui estava o erro: faltava isso)
            self.vegetation.draw_shadow(self.shadow_shader)

            # 3. Desenhar Personagens na Sombra (E isso)
            self.population.draw_shadow(self.shadow_shader)

            # Voltar para a tela normal
            self.shadow_mapper.unbind(self.width, self.height)

            # ---------- PASSO 2: RENDERIZAÇÃO DA CENA ----------
            
            glClearColor(self.sky_color.r, self.sky_color.g, self.sky_color.b, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            projection = glm.perspective(glm.radians(45.0), self.width / self.height, 0.1, 1000.0)
            view = self.camera.get_view_matrix()
            current_sky_color = (self.sky_color.r, self.sky_color.g, self.sky_color.b)

            # 1. Desenhar Terreno (Recebe Sombra)
            self.terrain_shader.use()
            self.terrain_shader.set_uniform_mat4("u_light_space_matrix", light_space_matrix)
            self.terrain_shader.set_uniform_int("u_shadow_map", 1)
            self.terrain_shader.set_uniform_vec3("u_sky_color", current_sky_color)
            
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.shadow_mapper.depth_map_texture)

            self.terrain.draw(self.camera, projection, self.sun_direction)
            self.render_with_outline(self.terrain, view, projection)

            # 2. Desenhar Vegetação
            self.vegetation.shader.use()
            self.vegetation.shader.set_uniform_vec3("u_sky_color", current_sky_color)
            self.vegetation.draw(view, projection, self.sun_direction, settings.COLOR_SUN, settings.COLOR_AMBIENT)
            self.render_with_outline(self.vegetation, view, projection)

            # 3. Desenhar População
            self.model_shader.use()
            self.model_shader.set_uniform_vec3("u_sky_color", current_sky_color)
            self.population.draw(self.model_shader, view, projection, self.sun_direction, light_space_matrix)

            # 4. Desenhar Água
            self.water.draw(view, projection, self.sky_color)
            
            # Atualizar animações
            self.population.update_animations(self.delta_time)

            # 5. Desenhar o Sol
            self.render_sun(projection)

            # 6. Desenhar HUD (Relógio)
            game_hour = (self.scene_time / 60.0) % 24.0
            hour = int(game_hour)
            minute = int((game_hour - hour) * 60)
            time_str = f"{hour:02d}:{minute:02d}"

            glDisable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.text_shader.use()
            self.text_shader.set_uniform_mat4("projection", self.hud_projection)
            self.text_shader.set_uniform_int("text", 0)
            self.text_renderer.render_text(self.text_shader, time_str, 20, self.height - 40, 1.0, (1.0, 1.0, 1.0))
            glDisable(GL_BLEND)
            glEnable(GL_DEPTH_TEST)

            glfw.swap_buffers(self.window)
            
        glfw.terminate()

    def mouse_callback(self, window, xpos, ypos):
        if self.first_mouse:
            self.last_mouse_x = xpos
            self.last_mouse_y = ypos
            self.first_mouse = False
        x_offset = xpos - self.last_mouse_x
        y_offset = self.last_mouse_y - ypos 
        self.last_mouse_x = xpos
        self.last_mouse_y = ypos
        self.camera.process_mouse_movement(x_offset, y_offset)

    def process_keyboard_input(self):
        if glfw.get_key(self.window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(self.window, True)
        multiplier = 1.0
        if glfw.get_key(self.window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS: 
            multiplier = settings.CAMERA_RUN_MULTIPLIER 
        velocity = settings.CAMERA_SPEED * multiplier * self.delta_time
        front_xz = glm.normalize(glm.vec3(self.camera.front.x, 0.0, self.camera.front.z))
        right_vector = glm.normalize(glm.cross(self.camera.front, self.camera.up))
        if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS: 
            self.camera.pos += front_xz * velocity 
        if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
            self.camera.pos -= front_xz * velocity
        if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS: 
            self.camera.pos -= right_vector * velocity 
        if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
            self.camera.pos += right_vector * velocity
        if glfw.get_key(self.window, glfw.KEY_SPACE) == glfw.PRESS:
            self.camera.jump()
        
    def render_sun(self, projection):
        self.sun_shader.use()
        sun_pos_world = self.camera.pos + self.sun_direction * 400.0
        view = self.camera.get_view_matrix()
        billboard_view = glm.mat4(glm.mat3(view))
        model = glm.translate(glm.mat4(1.0), sun_pos_world)
        model = model * glm.inverse(billboard_view)   
        model = glm.scale(model, glm.vec3(40.0, 40.0, 40.0)) 
        self.sun_shader.set_uniform_mat4("projection", projection)
        self.sun_shader.set_uniform_mat4("view", view)
        self.sun_shader.set_uniform_mat4("model", model)
        glBindVertexArray(self.sun_vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
    def update_day_night_cycle(self):
        self.scene_time += self.delta_time * 2
        game_hour = (self.scene_time / 60.0) % 24.0 
        angle = (game_hour / 24.0) * 2.0 * glm.pi()
        start_angle = angle - (glm.pi() / 2.0)
        self.sun_direction = glm.normalize(glm.vec3(glm.cos(start_angle), glm.sin(start_angle), 0.1))
        sun_height = self.sun_direction.y 
        if sun_height > 0.1: 
            factor = (sun_height - 0.1) / 0.9
            self.sky_color = glm.lerp(settings.COLOR_SUNSET, settings.COLOR_DAY, factor)
        elif sun_height > -0.1: 
            factor = (sun_height + 0.1) / 0.2
            self.sky_color = glm.lerp(settings.COLOR_NIGHT, settings.COLOR_SUNSET, factor)
        else: 
            self.sky_color = settings.COLOR_NIGHT

if __name__ == "__main__":
    engine = Engine(settings.WIN_WIDTH, settings.WIN_HEIGHT)
    print("Aplicação iniciada. Executando...")
    engine.run()
    print("Aplicação Finalizada.")