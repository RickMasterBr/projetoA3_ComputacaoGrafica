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
            image = Image.open(heightmap_path).convert('L') # Converte para Escala de Cinza
        except:
            print(f"ERRO: Não encontrei {heightmap_path}. Usando plano chato.")
            # Cria uma imagem 2x2 preta se falhar (fallback)
            image = Image.new('L', (2, 2), color=0)

        self.width, self.depth = image.size
        pixels = image.load()
        
        vertices = []
        indices = []

        # Gerar Vértices (Iterar pixel por pixel)
        # Centralizando o terreno para (0,0,0) ficar no meio
        start_x = -settings.TERRAIN_SIZE / 2.0
        start_z = -settings.TERRAIN_SIZE / 2.0
        
        step_x = settings.TERRAIN_SIZE / float(self.width - 1)
        step_z = settings.TERRAIN_SIZE / float(self.depth - 1)

        self.heights = [[0.0 for _ in range(self.depth)] for _ in range(self.width)]

        print("Gerando terreno... aguarde.")

        for i in range(self.depth):     # Z (Linhas da imagem)
            for j in range(self.width): # X (Colunas da imagem)
                
                # Calcular posição X, Z
                x = start_x + (j * step_x)
                z = start_z + (i * step_z)
                
                # Calcular altura Y (0 a 255 da imagem -> 0 a MAX_HEIGHT)
                y = (pixels[j, i] / 255.0) * settings.MAX_TERRAIN_HEIGHT
                self.heights[j][i] = y # Armazena para física
                
                # Adicionar vértice (x, y, z)
                vertices.extend([x, y, z])

        # Gerar Índices (Conectar os pontos em triângulos)
        for i in range(self.depth - 1):
            for j in range(self.width - 1):
                
                # vértices do quadrado atual
                top_left = (i * self.width) + j
                top_right = top_left + 1
                bottom_left = ((i + 1) * self.width) + j
                bottom_right = bottom_left + 1
                
                # Dois triângulos
                indices.extend([top_left, bottom_left, top_right])
                indices.extend([top_right, bottom_left, bottom_right])

        self.indices_count = len(indices)

        # Enviar para GPU com Numpy
        vertex_data = np.array(vertices, dtype=np.float32)
        index_data = np.array(indices, dtype=np.uint32)

        glBindVertexArray(self.vao)

        # VBO (Dados dos vértices)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

        # EBO (Índices)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL_STATIC_DRAW)

        # Atributo 0: Posição (vec3)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindVertexArray(0)
        print(f"Terreno gerado com {len(vertices)//3} vértices.")

    def draw(self, camera, projection_matrix):
        self.shader.use()
        
        # Configurar matrizes
        # Model: Matriz identidade (terreno não se move)
        self.shader.set_uniform_mat4("model", glm.mat4(1.0))
        self.shader.set_uniform_mat4("view", camera.get_view_matrix())
        self.shader.set_uniform_mat4("projection", projection_matrix)
        
        # Desenhar
        glBindVertexArray(self.vao)
        # Wireframe (modo linhas) para ver melhor a geometria sem textura por enquanto
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE) 
        glDrawElements(GL_TRIANGLES, self.indices_count, GL_UNSIGNED_INT, None)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL) # Voltar ao normal
        glBindVertexArray(0)