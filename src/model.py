from OpenGL.GL import *
import numpy as np
import ctypes
import assimp_py

class Mesh:
    def __init__(self, vertices, indices):
        self.vertices = vertices
        self.indices = indices
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        self.setup_mesh()

    def setup_mesh(self):
        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        # Layout
        stride = 32 
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))

        glBindVertexArray(0)

    def draw(self, shader):
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

class Model:
    def __init__(self, path, shader):
        self.shader = shader
        self.meshes = []
        self.load_model(path)

    def load_model(self, path):
        print(f"Carregando modelo: {path}...")
        
        flags = assimp_py.Process_Triangulate | assimp_py.Process_FlipUVs | assimp_py.Process_GenNormals
        
        try:
            # import_file
            scene = assimp_py.import_file(path, flags)
            
            # Detecção automática do nome do nó raiz
            if hasattr(scene, 'root_node'):
                self.process_node(scene.root_node, scene)
            elif hasattr(scene, 'rootnode'):
                self.process_node(scene.rootnode, scene)
            else:
                # Tenta pegar o primeiro atributo que parece um Node
                print("Aviso: Tentando adivinhar nó raiz...")
                self.process_node(scene.mRootNode, scene) # Tenta nome C++

            print(f"Modelo carregado: {len(self.meshes)} malhas.")
        except Exception as e:
            print(f"ERRO ao carregar modelo: {e}")

    def process_node(self, node, scene):
        # Usar 'mesh_indices' em vez de 'meshes'
        if hasattr(node, 'mesh_indices'):
            for mesh_index in node.mesh_indices:
                mesh = scene.meshes[mesh_index]
                self.meshes.append(self.process_mesh(mesh, scene))
        
        # Repete para os filhos
        for child in node.children:
            self.process_node(child, scene)

    def process_mesh(self, mesh, scene):
        # Conversão de dados para Numpy
        positions = np.array(mesh.vertices, dtype=np.float32)
        
        if mesh.normals:
            normals = np.array(mesh.normals, dtype=np.float32)
        else:
            normals = np.zeros((len(positions), 3), dtype=np.float32)
            
        # Verifica nome correto para coordenadas de textura
        tex_coords = np.zeros((len(positions), 2), dtype=np.float32)
        
        # Tenta nomes diferentes que a biblioteca pode usar
        coords = None
        if hasattr(mesh, 'texturecoords') and mesh.texturecoords:
            coords = mesh.texturecoords[0]
        elif hasattr(mesh, 'texture_coords') and mesh.texture_coords:
            coords = mesh.texture_coords[0]
            
        if coords is not None and len(coords) > 0:
             # Pega apenas U,V (ignora W se existir)
             # Se vier como lista de listas [[u,v,w],...], converte
             arr = np.array(coords, dtype=np.float32)
             if arr.shape[1] >= 2:
                 tex_coords = arr[:, :2]

        # Intercalar dados
        data = []
        for i in range(len(positions)):
            data.extend(positions[i])
            data.extend(normals[i])
            data.extend(tex_coords[i])
            
        vertex_data = np.array(data, dtype=np.float32)
        
        indices = []
        for face in mesh.faces:
            indices.extend(face)
        index_data = np.array(indices, dtype=np.uint32)

        return Mesh(vertex_data, index_data)

    def draw(self, shader):
        for mesh in self.meshes:
            mesh.draw(shader)