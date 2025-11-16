import numpy as np
from OpenGL.GL import *
from PIL import Image
import glm
import settings

class Terrain:
    def __init__(self, shader):
        self.shader = shader
        self.vertex_count = 0
        self.width = 0
        self.depth = 0
        self.heights = [] # Para física futura
        
        # VAO/VBO Handles
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        
        # Carregar e Gerar
        self.generate_terrain("assets/textures/heightmap.jpg")

    def generate_terrain(self, heightmap_path):
        # Carregar imagem
        try:
            image = Image.open(heightmap_path).convert('L')
        except Exception as e:
            print(f"ERRO: Não encontrei {heightmap_path}. Usando plano chato.")
            image = Image.new('L', (2, 2), color=0)

        self.width, self.depth = image.size
        pixels = image.load()
        
        self.heights = [[0.0 for _ in range(self.depth)] for _ in range(self.width)]
        
        # Listas para armazenar dados ---
        vertices_pos = [] # Armazena Posições (temporário)
        normals = []      # Armazena Normais (temporário)
        indices = []      # Armazena Índices
        
        # Array final que será enviado à GPU
        interleaved_data = [] 

        start_x = -settings.TERRAIN_SIZE / 2.0
        start_z = -settings.TERRAIN_SIZE / 2.0
        step_x = settings.TERRAIN_SIZE / float(self.width - 1)
        step_z = settings.TERRAIN_SIZE / float(self.depth - 1)

        print("Gerando terreno (Posições e Alturas)... aguarde.")
        
        # Gerar Posições de Vértices e armazenar alturas
        for i in range(self.depth):     # Z
            for j in range(self.width): # X
                x = start_x + (j * step_x)
                z = start_z + (i * step_z)
                y = (pixels[j, i] / 255.0) * settings.MAX_TERRAIN_HEIGHT
                
                self.heights[j][i] = y
                vertices_pos.append(glm.vec3(x, y, z)) # Adiciona Posição

        print("Calculando Normais...")
        
        # Helper para pegar altura de forma segura
        def get_height_safe(j, i):
            j_safe = max(0, min(j, self.width - 1))
            i_safe = max(0, min(i, self.depth - 1))
            return self.heights[j_safe][i_safe]

        for i in range(self.depth):
            for j in range(self.width):
                height_l = get_height_safe(j - 1, i)
                height_r = get_height_safe(j + 1, i)
                height_t = get_height_safe(j, i - 1)
                height_b = get_height_safe(j, i + 1)
                
                normal = glm.vec3(height_l - height_r, 2.0, height_t - height_b)
                normals.append(glm.normalize(normal)) # Adiciona Normal

        # Gerar Índices
        for i in range(self.depth - 1):
            for j in range(self.width - 1):
                top_left = (i * self.width) + j
                top_right = top_left + 1
                bottom_left = ((i + 1) * self.width) + j
                bottom_right = bottom_left + 1
                indices.extend([top_left, bottom_left, top_right])
                indices.extend([top_right, bottom_left, bottom_right])

        self.indices_count = len(indices)

        # Combinar Posições e Normais no array final
        # Verifique se os vértices foram realmente gerados
        if not vertices_pos or not normals:
             print("ERRO: Vértices ou normais não foram gerados.")
             return # Impede de continuar com 0 vértices

        for i in range(len(vertices_pos)):
            interleaved_data.extend([vertices_pos[i].x, vertices_pos[i].y, vertices_pos[i].z])
            interleaved_data.extend([normals[i].x, normals[i].y, normals[i].z])
            
        # Enviar para GPU
        vertex_data_np = np.array(interleaved_data, dtype=np.float32)
        index_data_np = np.array(indices, dtype=np.uint32)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertex_data_np.nbytes, vertex_data_np, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data_np.nbytes, index_data_np, GL_STATIC_DRAW)

        stride = 6 * 4
        
        # Atributo 0: Posição (vec3)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Atributo 1: Normal (vec3)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)
        
        print(f"Terreno gerado com {len(vertices_pos)} vértices.")

    def draw(self, camera, projection_matrix, sun_direction):
        self.shader.use()
        
        # Configurar matrizes
        # Model: Matriz identidade (terreno não se move)
        self.shader.set_uniform_mat4("model", glm.mat4(1.0))
        self.shader.set_uniform_mat4("view", camera.get_view_matrix())
        self.shader.set_uniform_mat4("projection", projection_matrix)
        
        # Passar dados de iluminação para o shader
        self.shader.set_uniform_vec3("u_sun_direction", sun_direction)
        self.shader.set_uniform_vec3("u_sun_color", settings.COLOR_SUN)
        self.shader.set_uniform_vec3("u_ambient_color", settings.COLOR_AMBIENT)

        # Desenhar
        glBindVertexArray(self.vao)

        glDrawElements(GL_TRIANGLES, self.indices_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def get_height(self, world_x, world_z):
        """ Converte coordenadas do mundo em altura do terreno. """

        # Converter coordenada do mundo (ex: -150 a +150) para 0.0-1.0
        percent_x = (world_x + (settings.TERRAIN_SIZE / 2.0)) / settings.TERRAIN_SIZE
        percent_z = (world_z + (settings.TERRAIN_SIZE / 2.0)) / settings.TERRAIN_SIZE

        # Converter 0.0-1.0 para índice do array (ex: 0 a 1023)
        map_j = int(percent_x * (self.width - 1)) # Coluna
        map_i = int(percent_z * (self.depth - 1)) # Linha

        # Verificar limites
        map_j = max(0, min(self.width - 2, map_j))
        map_i = max(0, min(self.depth - 2, map_i))

        # Retornar altura armazenada
        # (Adicionamos um 'buffer' de 0.2m para evitar que a câmera entre no chão)
        return self.heights[map_j][map_i] + 0.2