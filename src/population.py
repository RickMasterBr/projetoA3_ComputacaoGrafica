import glm
import random
import math
from OpenGL.GL import *
from settings import COLOR_SUN, COLOR_AMBIENT # Importar configurações globais

class Population:
    def __init__(self, terrain, models, count=80):
        """
        terrain: Instância do terreno (para pegar altura)
        models: Lista com os 4 objetos Model carregados (character, abe, jackie, michelle)
        count: Total de personagens a espalhar (padrão 80)
        """
        self.terrain = terrain
        self.models = models
        self.count = count
        self.instances = [] # Lista de dicionários {'model_idx': 0, 'matrix': mat4}
        
        self.spawn_crowd()

    def spawn_crowd(self):
        print(f"Populando o mundo com {self.count} personagens...")
        generated = 0
        attempts = 0
        spawn_radius = 260 # Um pouco menos que as árvores para ficarem mais no centro
        
        while generated < self.count and attempts < self.count * 10:
            attempts += 1
            
            # 1. Posição Aleatória (Circular)
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(10, spawn_radius) # 10m min para não nascer EM CIMA da camera
            x = math.cos(angle) * dist
            z = math.sin(angle) * dist
            
            # 2. Altura do Terreno
            try:
                y = self.terrain.get_height(x, z)
            except:
                continue

            # 3. Validação (Não spawnar na água ou em picos muito íngremes)
            if y < 15 or y > 85:
                continue
                
            # 4. Escolher modelo aleatório (0 a 3)
            model_idx = random.randint(0, len(self.models) - 1)
            
            # 5. Rotação aleatória (para não ficarem todos virados pro mesmo lado)
            rot_y = random.uniform(0, 360)
            
            # 6. Criar Matriz de Modelo (Model Matrix)
            # Ordem: Translate -> Rotate -> Scale
            mat = glm.mat4(1.0)
            mat = glm.translate(mat, glm.vec3(x, y, z))
            mat = glm.rotate(mat, glm.radians(rot_y), glm.vec3(0, 1, 0))
            mat = glm.scale(mat, glm.vec3(2.0, 2.0, 2.0)) # Escala 2.0 igual usava no main
            
            self.instances.append({
                'model_idx': model_idx,
                'matrix': mat
            })
            
            generated += 1
            
        print(f"Sucesso! {generated} personagens posicionados.")

    def draw(self, shader, view, projection, sun_direction, light_space_matrix):
        """
        Desenha todos os 80 personagens usando o shader fornecido.
        """
        shader.use()
        
        # Configurar Uniforms Globais (Vêm do settings ou main)
        shader.set_uniform_mat4("view", view)
        shader.set_uniform_mat4("projection", projection)
        shader.set_uniform_vec3("u_sun_direction", sun_direction)
        shader.set_uniform_vec3("u_sun_color", COLOR_SUN)
        shader.set_uniform_vec3("u_ambient_color", COLOR_AMBIENT)
        shader.set_uniform_mat4("u_light_space_matrix", light_space_matrix)
        shader.set_uniform_int("u_shadow_map", 1) # Slot da textura de sombra

        # Renderizar cada instância
        for instance in self.instances:
            idx = instance['model_idx']
            model_matrix = instance['matrix']
            
            # Enviar matrix individual
            shader.set_uniform_mat4("model", model_matrix)
            
            # Desenhar o modelo correspondente
            self.models[idx].draw(shader)

    def update_animations(self, delta_time):
        # Atualiza a animação dos 4 modelos base
        # (Como são instâncias, todos do mesmo tipo vão se mexer igual/sincronizado, 
        #  o que é aceitável para performance em Python)
        for model in self.models:
            model.update_animation(delta_time)

    # --- NOVO MÉTODO: Desenha sombra dos personagens ---
    def draw_shadow(self, shader):
        # Renderiza a geometria de todos os personagens no mapa de sombra
        for instance in self.instances:
            idx = instance['model_idx']
            model_matrix = instance['matrix']
            shader.set_uniform_mat4("model", model_matrix)
            self.models[idx].draw(shader)