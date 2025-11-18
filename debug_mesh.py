import assimp_py
import sys

path = "assets/models/character.fbx"

try:
    print(f"Carregando {path}...")
    # Flags padrão
    flags = assimp_py.Process_Triangulate | assimp_py.Process_GenNormals
    scene = assimp_py.import_file(path, flags)
    
    if len(scene.meshes) > 0:
        mesh = scene.meshes[0]
        print("-" * 30)
        print("ATRIBUTOS DA MALHA (MESH):")
        print("-" * 30)
        # Lista todos os atributos disponíveis na malha
        print(dir(mesh))
        print("-" * 30)
    else:
        print("Nenhuma malha encontrada no arquivo.")

except Exception as e:
    print(f"Erro: {e}")