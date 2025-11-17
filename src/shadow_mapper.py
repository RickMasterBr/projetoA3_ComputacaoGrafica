from OpenGL.GL import *
import settings

class ShadowMapper:
    def __init__(self):
        # Criar o Framebuffer Object (FBO)
        self.depth_map_fbo = glGenFramebuffers(1)

        # Criar a textura de profundidade (O mapa)
        self.depth_map_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_map_texture)

        # Confugurar a textura para armazenar apenas a profundidade
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT,
                      settings.SHADOW_MAP_WIDTH,
                      settings.SHADOW_MAP_HEIGHT,
                      0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        
        # configurar parâmetros da textura pra nao repetir a sombra errada
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

        # Borda branca para áreas fora do mapa (Sem sombra)
        border_color = [1.0, 1.0, 1.0, 1.0]
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)

        # anexar textura ao FBO
        glBindFramebuffer(GL_FRAMEBUFFER, self.depth_map_fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                               GL_TEXTURE_2D, self.depth_map_texture, 0)
        
        # Dizer ao opgenl que não vamos desenhar cor, apenas profundidade
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        
        # Verificar se deu certo
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Erro: Framebuffer de sombra não está completo!")
            
        glBindFramebuffer(GL_FRAMEBUFFER, 0) # Voltar ao normal

    def bind(self):
        """Ativa o modo de renderização de sombra."""
        glViewport(0, 0, settings.SHADOW_MAP_WIDTH, settings.SHADOW_MAP_HEIGHT)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depth_map_fbo)
        glClear(GL_DEPTH_BUFFER_BIT)

    def unbind(self, win_width, win_height):
        """Volta para o modo de renderização normal."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, win_width, win_height)