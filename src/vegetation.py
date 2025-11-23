import glm
import random
import math
import ctypes
from OpenGL.GL import *
import numpy as np
from shader import Shader  # Importação corrigida (sem 'src.')

class Vegetation:
    def __init__(self, terrain, count=150):
        self.terrain = terrain
        self.count = count
        self.vertices = []
        
        # Shader dedicado para vegetação
        self.shader = Shader("shaders/vegetation.vert", "shaders/vegetation.frag")
        
        self.generate_forest()
        self.setup_buffers()

    def generate_forest(self):
        print(f"Gerando {self.count} arvores low-poly...")
        generated = 0
        attempts = 0
        
        spawn_radius = 280 
        
        while generated < self.count and attempts < self.count * 10:
            attempts += 1
            
            # Posição Aleatória
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, spawn_radius)
            x = math.cos(angle) * dist
            z = math.sin(angle) * dist
            
            # Pegar altura do terreno nesta posição
            # Usa o método get_height do seu terrain.py
            try:
                y = self.terrain.get_height(x, z)
            except:
                y = 0 # Fallback caso dê erro
            
            # Regras de Spawn: Evitar água e picos muito altos
            if y < 15 or y > 80:
                continue
                
            self.add_tree(x, y, z)
            generated += 1
            
    def add_tree(self, x, y, z):
        # Configuração da Árvore
        trunk_color = [0.4, 0.25, 0.1] # Marrom escuro
        
        # Variação na cor das folhas
        green_var = random.uniform(0.0, 0.2)
        leaf_color = [0.1, 0.6 + green_var, 0.2] 
        
        scale = random.uniform(0.8, 1.5)
        
        # 1. TRONCO 
        self.add_cylinder(x, y, z, 0.6 * scale, 3.0 * scale, trunk_color)
        
        # 2. COPA (3 Pirâmides)
        self.add_cone(x, y + 2.5*scale, z, 2.5*scale, 2.5*scale, leaf_color) # Baixo
        self.add_cone(x, y + 4.5*scale, z, 2.0*scale, 2.5*scale, leaf_color) # Meio
        self.add_cone(x, y + 6.5*scale, z, 1.5*scale, 2.0*scale, leaf_color) # Topo

    def add_cylinder(self, cx, cy, cz, radius, height, color):
        segments = 6 # Hexagonal (Low Poly)
        angle_step = (math.pi * 2) / segments
        
        for i in range(segments):
            angle1 = i * angle_step
            angle2 = (i + 1) * angle_step
            
            x1 = cx + math.cos(angle1) * radius
            z1 = cz + math.sin(angle1) * radius
            x2 = cx + math.cos(angle2) * radius
            z2 = cz + math.sin(angle2) * radius
            
            # Normal (flat shading)
            nx = math.cos(angle1 + angle_step/2)
            nz = math.sin(angle1 + angle_step/2)
            
            # Triangulo 1
            self.vertices.extend([x1, cy, z1] + color + [nx, 0, nz])
            self.vertices.extend([x2, cy, z2] + color + [nx, 0, nz])
            self.vertices.extend([x1, cy+height, z1] + color + [nx, 0, nz])
            
            # Triangulo 2
            self.vertices.extend([x1, cy+height, z1] + color + [nx, 0, nz])
            self.vertices.extend([x2, cy, z2] + color + [nx, 0, nz])
            self.vertices.extend([x2, cy+height, z2] + color + [nx, 0, nz])

    def add_cone(self, cx, cy, cz, radius, height, color):
        segments = 6 
        angle_step = (math.pi * 2) / segments
        
        top_point = [cx, cy + height, cz]
        
        for i in range(segments):
            angle1 = i * angle_step
            angle2 = (i + 1) * angle_step
            
            x1 = cx + math.cos(angle1) * radius
            z1 = cz + math.sin(angle1) * radius
            x2 = cx + math.cos(angle2) * radius
            z2 = cz + math.sin(angle2) * radius
            
            # Calcular Normal da Face
            ux, uy, uz = x2-x1, 0, z2-z1
            vx, vy, vz = top_point[0]-x1, top_point[1]-cy, top_point[2]-z1
            
            nx = uy*vz - uz*vy
            ny = uz*vx - ux*vz
            nz = ux*vy - uy*vx
            
            l = math.sqrt(nx*nx + ny*ny + nz*nz)
            if l == 0: l = 1
            nx, ny, nz = nx/l, ny/l, nz/l
            
            self.vertices.extend([x1, cy, z1] + color + [nx, ny, nz])
            self.vertices.extend([x2, cy, z2] + color + [nx, ny, nz])
            self.vertices.extend(top_point + color + [nx, ny, nz])

    def setup_buffers(self):
        self.vertices = np.array(self.vertices, dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        
        stride = 9 * 4 
        
        # Position (loc 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        
        # Color (loc 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        
        # Normal (loc 2)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))

    def draw(self, view, projection, sun_direction, sun_color, ambient_color):
        self.shader.use()
        
        # --- CORREÇÃO AQUI ---
        # Usando os nomes corretos do seu shader.py (set_uniform_mat4 em vez de set_mat4)
        self.shader.set_uniform_mat4("view", view)
        self.shader.set_uniform_mat4("projection", projection)
        self.shader.set_uniform_mat4("model", glm.mat4(1.0)) 
        
        # Usando os métodos corretos para vetores (set_uniform_vec3)
        self.shader.set_uniform_vec3("u_sun_direction", sun_direction)
        self.shader.set_uniform_vec3("u_sun_color", sun_color)
        self.shader.set_uniform_vec3("u_ambient_color", ambient_color)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 9)