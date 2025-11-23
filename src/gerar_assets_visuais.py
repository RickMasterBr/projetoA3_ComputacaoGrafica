from PIL import Image, ImageDraw, ImageFilter
import math
import os

# Garante diretórios
os.makedirs("assets/textures", exist_ok=True)

# 1. HEIGHTMAP SUAVIZADO (Curvas amplas)
def generate_smooth_heightmap():
    size = 1024
    img = Image.new('L', (size, size), 0)
    pixels = img.load()
    center = size / 2
    
    # Gera uma ilha cônica suave
    for x in range(size):
        for y in range(size):
            dx, dy = x - center, y - center
            dist = math.sqrt(dx*dx + dy*dy) / (size/2)
            
            # Curva suave (cosseno)
            if dist < 1.0:
                h = (math.cos(dist * math.pi) + 1) * 0.5
                # Adiciona "ruído" suave desenhado
                noise = (math.sin(x * 0.05) + math.cos(y * 0.05)) * 0.02
                pixels[x,y] = int((h + noise) * 255)
            else:
                pixels[x,y] = 0
                
    # Blur para tirar pontas
    img = img.filter(ImageFilter.GaussianBlur(radius=10))
    img.save("assets/textures/heightmap.jpg")
    print("Heightmap suave gerado.")

# 2. SOL ESTILIZADO (Sprite 2D)
def generate_sun_sprite():
    size = 512
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Halo externo
    draw.ellipse([50, 50, 462, 462], fill=(255, 240, 200, 100))
    # Núcleo branco irregular
    draw.ellipse([100, 100, 412, 412], fill=(255, 255, 255, 255))
    
    # Blur para ficar "fofinho"
    img = img.filter(ImageFilter.GaussianBlur(radius=20))
    img.save("assets/textures/sun_sprite.png")
    print("Sol estilizado gerado.")

if __name__ == "__main__":
    generate_smooth_heightmap()
    generate_sun_sprite()