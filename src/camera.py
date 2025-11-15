import glm
import settings

class Camera:
    def __init__(self, position=glm.vec3(0,0,3)):

        # posição e direção da câmera
        self.pos = position
        self.front = glm.vec3(0,0,-1) # olhando para -Z
        self.up = glm.vec3(0,1,0) # Eixo Y é para cima

        # ângulos de Euler ( para o mouse )
        self.yaw = -90.0 # Yaw vira para a esquerda e direita
        self.pitch = 0.0 # Pitch olha para cima e para baixo

        # Variáveis de Física
        self.y_velocity = 0.0
        self.on_ground = False

    def get_view_matrix(self):
        """Calcula e Retorna a matriz 'view' da câmera (LookAt)."""
        return glm.lookAt(self.pos, self.pos + self.front, self.up)
    
    def process_mouse_movement(self, x_offset, y_offset):
        """Processa o movimento do mouse para atualizar yaw e pitch."""
        
        x_offset *= settings.CAMERA_SENSITIVITY
        y_offset *= settings.CAMERA_SENSITIVITY

        self.yaw += x_offset
        self.pitch += y_offset

        # Restringir o pitch
        self.pitch = glm.clamp(self.pitch, -89.0, 89.0) #

        # Recalcular o vetor 'front'
        front_vec = glm.vec3()
        front_vec.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch)) #
        front_vec.y = glm.sin(glm.radians(self.pitch)) #
        front_vec.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch)) #
        self.front = glm.normalize(front_vec)