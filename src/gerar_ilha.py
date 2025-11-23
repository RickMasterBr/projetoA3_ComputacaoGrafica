from PIL import Image
import math

# Configurações da Ilha
SIZE = 1024          # Tamanho da imagem
CENTER = SIZE / 2

# AJUSTE 1: Aumentamos a área garantidamente plana (era 300)
RADIUS_FLAT = 340    

# AJUSTE 2: Aumentamos o limite da ilha para usar mais espaço da imagem (era 480)
# Isso ajuda a distribuir a inclinação por uma área maior.
RADIUS_MAX = 510     

img = Image.new('L', (SIZE, SIZE), color=0) # Cria imagem preta (fundo do mar)
pixels = img.load()

print("Gerando heightmap... aguarde um momento.")

for x in range(SIZE):
    for y in range(SIZE):
        # Distância do pixel até o centro
        dx = x - CENTER
        dy = y - CENTER
        distance = math.sqrt(dx*dx + dy*dy)

        if distance < RADIUS_FLAT:
            # Centro totalmente plano (Platô)
            pixels[x, y] = 255
            
        elif distance < RADIUS_MAX:
            # Zona de transição (Borda caindo)
            
            # 'factor' vai de 0.0 (início da queda) até 1.0 (fim da ilha)
            factor = (distance - RADIUS_FLAT) / (RADIUS_MAX - RADIUS_FLAT)
            
            # --- O TRUQUE MATEMÁTICO ---
            # Elevamos o fator ao quadrado (ou cubo). 
            # Isso faz com que o número permaneça pequeno no início e cresça rápido no final.
            # Resultado: A ilha mantém a altura por mais tempo e cai só na borda final.
            # Tenta alterar para 3.0 se quiseres ainda mais plano!
            factor = math.pow(factor, 2.0)
            
            # Usar coseno para a curva S suave
            height = (math.cos(factor * math.pi) + 1) / 2 
            
            pixels[x, y] = int(height * 255)
        else:
            # Mar/Vazio
            pixels[x, y] = 0

# Salva na pasta de texturas
try:
    path = "assets/textures/heightmap.jpg"
    img.save(path)
    print(f"Sucesso! Heightmap atualizado e salvo em '{path}'")
except FileNotFoundError:
    img.save("heightmap.jpg") 
    print("AVISO: Pasta 'assets/textures' não encontrada. Imagem salva na raiz como 'heightmap.jpg'.")