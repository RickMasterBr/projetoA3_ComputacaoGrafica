import glm
import random
import math
import ctypes
from OpenGL.GL import *
import numpy as np
from shader import Shader

class Vegetation:
    def __init__(self, terrain, count=150):
        self.tree_positions = [] 
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
            try:
                y = self.terrain.get_height(x, z)
            except:
                y = 0 # Fallback
            
            # Regras de Spawn: Evitar água e picos muito altos
            if y < 15 or y > 80:
                continue
                
            self.add_tree(x, y, z)
            generated += 1

            # Mantendo sua lógica original das pedras
            for _ in range(100):
                # Desenhe uma "Pedra Low Poly" (Um cone achatado cinza)
                stone_color = [0.6, 0.6, 0.65] # Cinza azulado
                self.add_cone(x, y, z, radius=random.uniform(1.0, 2.0), height=random.uniform(0.5, 1.0), color=stone_color)

    def add_tree(self, x, y, z):
        # Cores Pastel
        trunk_color = [0.55, 0.45, 0.40] # Marrom acinzentado
        leaf_color  = [0.48, 0.77, 0.63] # Verde menta
        
        scale = random.uniform(1.2, 2.5)
        
        # 1. TRONCO
        self.add_cylinder(x, y, z, 0.5 * scale, 2.0 * scale, trunk_color)
        
        # 2. COPA
        self.add_cone(x, y + 1.5*scale, z, 2.5*scale, 2.0*scale, leaf_color)
        self.add_cone(x, y + 3.0*scale, z, 1.8*scale, 1.5*scale, leaf_color)
        
        # Opcional: Adicionar uma pedra pequena na base
        if random.random() > 0.7:
            self.add_cone(x + 1.0, y, z + 0.5, 0.8, 0.6, [0.5, 0.5, 0.6])

        # Guardar posição para colisão
        self.tree_positions.append((x, z, 1.0))
   
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
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))

    def draw(self, view, projection, sun_direction, sun_color, ambient_color):
        self.shader.use()
        self.shader.set_uniform_mat4("view", view)
        self.shader.set_uniform_mat4("projection", projection)
        self.shader.set_uniform_mat4("model", glm.mat4(1.0)) 
        
        self.shader.set_uniform_vec3("u_sun_direction", sun_direction)
        self.shader.set_uniform_vec3("u_sun_color", sun_color)
        self.shader.set_uniform_vec3("u_ambient_color", ambient_color)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 9)

    # --- NOVO: Método necessário para desenhar a sombra das árvores ---
    def draw_shadow(self, shader):
        # A matriz model é identidade pois as árvores já têm posição fixa no mundo
        shader.set_uniform_mat4("model", glm.mat4(1.0))
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 9)
        glBindVertexArray(0)