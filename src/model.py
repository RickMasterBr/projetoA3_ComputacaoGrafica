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

        # Layout (Stride = 32 bytes: 3 pos + 3 norm + 2 tex)
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
        # Flags: Triangulate e GenNormals são essenciais
        flags = assimp_py.Process_Triangulate | assimp_py.Process_FlipUVs | assimp_py.Process_GenNormals | assimp_py.Process_JoinIdenticalVertices
        
        try:
            scene = assimp_py.import_file(path, flags)
            
            # Detecta nome do nó raiz
            root = None
            if hasattr(scene, 'root_node'): root = scene.root_node
            elif hasattr(scene, 'rootnode'): root = scene.rootnode
            else: root = scene.mRootNode # Tentativa final
            
            self.process_node(root, scene)
            print(f"Modelo carregado: {len(self.meshes)} malhas.")
            
        except Exception as e:
            print(f"ERRO CRÍTICO ao carregar modelo: {e}")
            raise

    def process_node(self, node, scene):
        # Nome correto para lista de índices de malha: mesh_indices
        if hasattr(node, 'mesh_indices'):
            for mesh_index in node.mesh_indices:
                mesh = scene.meshes[mesh_index]
                self.meshes.append(self.process_mesh(mesh, scene))
        
        for child in node.children:
            self.process_node(child, scene)

    def process_mesh(self, mesh, scene):
        # 1. Vértices
        positions = np.array(mesh.vertices, dtype=np.float32)
        if positions.ndim == 1: positions = positions.reshape(-1, 3)
        
        # 2. Normais
        if mesh.normals:
            normals = np.array(mesh.normals, dtype=np.float32)
            if normals.ndim == 1: normals = normals.reshape(-1, 3)
        else:
            normals = np.zeros((len(positions), 3), dtype=np.float32)
            
        # 3. Texturas (Nome correto: texcoords)
        tex_coords = np.zeros((len(positions), 2), dtype=np.float32)
        
        # A biblioteca pode retornar uma lista de canais ou None
        if hasattr(mesh, 'texcoords') and mesh.texcoords:
            # Pega o primeiro canal de textura (index 0)
            channel0 = mesh.texcoords[0]
            if channel0 is not None:
                arr = np.array(channel0, dtype=np.float32)
                # Garante formato (N, 2) ou (N, 3)
                if arr.ndim == 1:
                     # Tenta adivinhar o formato baseado no tamanho
                     if arr.size == len(positions) * 2: arr = arr.reshape(-1, 2)
                     elif arr.size == len(positions) * 3: arr = arr.reshape(-1, 3)
                
                if arr.ndim == 2 and arr.shape[1] >= 2:
                    tex_coords = arr[:, :2] # Pega só U e V

        # 4. Intercalar (Position + Normal + UV)
        data = []
        # Otimização: Usar numpy direto é mais rápido que loop for
        # Formato: [px, py, pz, nx, ny, nz, u, v]
        # Stack horizontalmente
        interleaved = np.hstack((positions, normals, tex_coords))
        vertex_data = interleaved.flatten().astype(np.float32)
        
        # 5. Índices (Nome correto: indices)
        # A biblioteca já entrega a lista pronta!
        index_data = np.array(mesh.indices, dtype=np.uint32)

        return Mesh(vertex_data, index_data)

    def draw(self, shader):
        for mesh in self.meshes:
            mesh.draw(shader)