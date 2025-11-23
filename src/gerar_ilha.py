from PIL import Image
import math

# Configurações da Ilha
SIZE = 1024          # Tamanho da imagem (1024x1024 é bom para performance)
CENTER = SIZE / 2
RADIUS_FLAT = 300    # Raio onde o chão é 100% plano (Área jogável)
RADIUS_MAX = 480     # Raio onde a ilha termina e cai para o mar

img = Image.new('L', (SIZE, SIZE), color=0) # Cria imagem preta
pixels = img.load()

for x in range(SIZE):
    for y in range(SIZE):
        # Distância do pixel até o centro
        dx = x - CENTER
        dy = y - CENTER
        distance = math.sqrt(dx*dx + dy*dy)

        if distance < RADIUS_FLAT:
            # Centro plano
            pixels[x, y] = 255
        elif distance < RADIUS_MAX:
            # Borda caindo (Curva suave para parecer rocha natural)
            factor = (distance - RADIUS_FLAT) / (RADIUS_MAX - RADIUS_FLAT)
            # Usar coseno para uma curva mais arredondada tipo "Super Mario Galaxy"
            height = (math.cos(factor * math.pi) + 1) / 2 
            pixels[x, y] = int(height * 255)
        else:
            # Mar/Vazio
            pixels[x, y] = 0

# Salva na pasta de texturas (ajuste o caminho se necessário)
try:
    img.save("assets/textures/heightmap.jpg")
    print("Sucesso! Heightmap de Ilha Flutuante criado em 'assets/textures/heightmap.jpg'")
except FileNotFoundError:
    # Caso a pasta não exista, salva na raiz pra vc mover depois
    img.save("heightmap.jpg") 
    print("Pasta assets não achada. Imagem salva na raiz como 'heightmap.jpg'. Mova-a para assets/textures/")