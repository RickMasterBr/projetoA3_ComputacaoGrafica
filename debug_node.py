import assimp_py
import sys

try:
    # Carrega o modelo
    flags = assimp_py.Process_Triangulate
    scene = assimp_py.import_file("assets/models/character.fbx", flags)
    
    # Pega o nó raiz
    node = scene.root_node
    
    print("-" * 30)
    print("ATRIBUTOS DO NÓ (NODE):")
    print("-" * 30)
    
    # Lista tudo o que tem dentro do 'node'
    print(dir(node))
    
    print("-" * 30)
    
except Exception as e:
    print(f"Erro: {e}")