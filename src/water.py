from OpenGL.GL import *
import ctypes
import numpy as np
import glm
from shader import Shader

class Water:
    def __init__(self, size=1000, height=12.0):
        self.height = height
        
        # Shader simples para água (usa cor sólida + transparência)
        self.shader = Shader("shaders/water.vert", "shaders/water.frag")
        
        # Cria um quadrado gigante (2 triângulos)
        # x, y, z
        vertices = [
            -size, height, -size,
             size, height, -size,
             size, height,  size,
            
             size, height,  size,
            -size, height,  size,
            -size, height, -size
        ]
        
        self.vertices = np.array(vertices, dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        
        # Apenas Posição (layout 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        
    def draw(self, view, projection, sky_color):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.shader.use()
        self.shader.set_uniform_mat4("view", view)
        self.shader.set_uniform_mat4("projection", projection)
        self.shader.set_uniform_mat4("model", glm.mat4(1.0))
        
        # Cor da água (Azul profundo) misturada com o céu
        water_color = glm.vec3(0.1, 0.3, 0.8) 
        self.shader.set_uniform_vec3("u_color", water_color)
        self.shader.set_uniform_vec3("u_sky_color", sky_color)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        glDisable(GL_BLEND)