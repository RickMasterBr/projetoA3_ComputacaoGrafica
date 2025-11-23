import glm
import settings

class Camera:
    def __init__(self, position=glm.vec3(0, 10, 3)):
        # Posição inicial (mais alta para não nascer dentro do chão)
        self.pos = position
        self.front = glm.vec3(0, 0, -1)
        self.up = glm.vec3(0, 1, 0)

        # Configurações do Jogador
        self.player_height = 2.0  # Altura dos olhos (2 metros)
        self.jump_force = 15.0    # Força do pulo
        self.gravity = 40.0       # Gravidade (ajustada para parecer real)

        # Controles de Mouse
        self.yaw = -90.0
        self.pitch = 0.0

        # Variáveis de Física
        self.y_velocity = 0.0
        self.on_ground = False

    def get_view_matrix(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.up)
    
    def process_mouse_movement(self, x_offset, y_offset):
        x_offset *= settings.CAMERA_SENSITIVITY
        y_offset *= settings.CAMERA_SENSITIVITY

        self.yaw += x_offset
        self.pitch += y_offset

        # Limitar o olhar para cima/baixo (não quebrar o pescoço)
        self.pitch = glm.clamp(self.pitch, -89.0, 89.0)

        # Recalcular vetor da frente
        front_vec = glm.vec3()
        front_vec.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        front_vec.y = glm.sin(glm.radians(self.pitch))
        front_vec.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front = glm.normalize(front_vec)

    def update_physics(self, delta_time, terrain):
        """Aplica gravidade e mantém o jogador acima do terreno."""
        
        # 1. Aplicar Gravidade
        self.y_velocity -= self.gravity * delta_time
        
        # 2. Mover Verticalmente
        self.pos.y += self.y_velocity * delta_time

        # 3. Colisão com o Terreno
        # Pegamos a altura do chão na posição X, Z atual
        try:
            ground_height = terrain.get_height(self.pos.x, self.pos.z)
        except:
            ground_height = 0.0 # Segurança se sair do mapa
            
        # A altura mínima permitida é Chão + Altura do Jogador
        min_height = ground_height + self.player_height
        
        # Se cair abaixo do chão, corrigir
        if self.pos.y < min_height:
            self.pos.y = min_height
            self.y_velocity = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

    def jump(self):
        """Pula apenas se estiver no chão."""
        if self.on_ground:
            self.y_velocity = self.jump_force
            self.on_ground = False