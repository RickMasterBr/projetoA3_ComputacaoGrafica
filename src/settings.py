import glm

# Constantes globais

# dimensões da tela
WIN_WIDTH = 1280
WIN_HEIGHT = 720

# Constantes da física
GRAVITY = -9.8
JUMP_FORCE = 5.0

# Constantes de terreno
MAX_TERRAIN_HEIGHT = 40.0

# Novas Constantes da Câmera
CAMERA_SPEED = 5.0 # Metros por segundo
CAMERA_RUN_MULTIPLIER = 2.0
CAMERA_SENSITIVITY = 0.1

# Configurações do Terreno
TERRAIN_SIZE = 300.0 # O PDF pede >= 300m (Regra 1.a)

# Cores Pastel (Refinadas)
COLOR_DAY     = glm.vec3(0.53, 0.81, 0.92) # Sky Blue mais vivo (menos cinza)
COLOR_SUNSET  = glm.vec3(0.96, 0.70, 0.65) # Salmão suave
COLOR_NIGHT   = glm.vec3(0.05, 0.05, 0.15) # Azul meia-noite (não preto total)

# Luz (Reduzindo o branco estourado)
COLOR_SUN     = glm.vec3(1.00, 0.90, 0.70) # Amarelo manteiga suave
COLOR_AMBIENT = glm.vec3(0.60, 0.60, 0.70) # Ambiente azulado e forte (sombras claras)

# Configuraçõs de Sombra
SHADOW_MAP_WIDTH = 2048
SHADOW_MAP_HEIGHT = 2048
