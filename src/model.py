from OpenGL.GL import *
import numpy as np
import ctypes
import impasse
import glm

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
        
        # VBO
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        # EBO
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        # Layout (Stride = 64 bytes: 3 pos + 3 norm + 2 uv + 4 bone_id + 4 weight)
        stride = 64
        
        # 0: Posição
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        # 1: Normal
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        # 2: UV
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        # 3: Bone IDs (Inteiros!)
        glEnableVertexAttribArray(3)
        glVertexAttribIPointer(3, 4, GL_INT, stride, ctypes.c_void_p(32))
        # 4: Weights
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(48))

        glBindVertexArray(0)

    def draw(self, shader):
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

class Model:
    def __init__(self, path, shader):
        self.shader = shader
        self.meshes = []
        self.bone_map = {}
        self.bone_info = []
        self.bone_counter = 0
        self.load_model(path)

    def load_model(self, path):
        print(f"Carregando modelo (impasse): {path}...")
        try:
            # Impasse carrega direto (sem flags complexas, ele usa padrão bom)
            scene = impasse.load(path)
            
            # Tenta achar a raiz (rootnode ou mRootNode)
            root = getattr(scene, 'rootnode', getattr(scene, 'mRootNode', getattr(scene, 'root_node', None)))
            
            if root:
                self.process_node(root, scene)
                print(f"Modelo carregado! Malhas: {len(self.meshes)} | Ossos: {self.bone_counter}")
            else:
                print("ERRO CRÍTICO: Nó raiz não encontrado na cena.")
                
            scene.release()
            
        except Exception as e:
            print(f"ERRO CRÍTICO ao carregar modelo: {e}")
            # Não damos raise para não fechar a janela, mas o boneco não aparecerá

    def process_node(self, node, scene):
        # Tenta achar a lista de malhas (meshes ou mesh_indices)
        node_meshes = getattr(node, 'meshes', getattr(node, 'mesh_indices', []))
        
        for i in node_meshes:
            mesh = scene.meshes[i]
            self.meshes.append(self.process_mesh(mesh, scene))
        
        for child in node.children:
            self.process_node(child, scene)

    def process_mesh(self, mesh, scene):
        num_v = len(mesh.vertices)
        
        # 1. Vértices
        positions = np.array(mesh.vertices, dtype=np.float32)
        
        # 2. Normais
        if hasattr(mesh, 'normals') and len(mesh.normals) > 0:
            normals = np.array(mesh.normals, dtype=np.float32)
        else:
            normals = np.zeros((num_v, 3), dtype=np.float32)

        # 3. Texturas (Tenta 'texturecoords' do impasse)
        tex_coords = np.zeros((num_v, 2), dtype=np.float32)
        uv_channels = getattr(mesh, 'texturecoords', getattr(mesh, 'texcoords', None))
        
        if uv_channels and len(uv_channels) > 0 and uv_channels[0] is not None:
             uv = np.array(uv_channels[0], dtype=np.float32)
             # Se vier com 3 componentes (u,v,w), pega só 2
             if uv.shape[1] > 2: tex_coords = uv[:, :2]
             else: tex_coords = uv

        # 4. Ossos (Recuperado!)
        bone_ids = np.zeros((num_v, 4), dtype=np.int32)
        weights = np.zeros((num_v, 4), dtype=np.float32)

        if hasattr(mesh, 'bones'):
            for bone in mesh.bones:
                if bone.name not in self.bone_map:
                    self.bone_map[bone.name] = self.bone_counter
                    self.bone_counter += 1
                    # Transpor matriz para OpenGL (Column-Major)
                    offset = np.array(bone.offsetmatrix, dtype=np.float32).transpose()
                    self.bone_info.append(offset)
                
                b_id = self.bone_map[bone.name]
                for w in bone.weights:
                    if w.weight == 0.0: continue
                    for i in range(4):
                        if weights[w.vertexid][i] == 0.0:
                            weights[w.vertexid][i] = w.weight
                            bone_ids[w.vertexid][i] = b_id
                            break

        # 5. Índices (A CORREÇÃO PRINCIPAL)
        indices = []
        if hasattr(mesh, 'faces'):
             # Impasse usa 'faces', que é uma lista de listas. Precisamos aplanar.
             for face in mesh.faces:
                 indices.extend(face)
        elif hasattr(mesh, 'indices'):
             indices = mesh.indices
        
        index_data = np.array(indices, dtype=np.uint32)

        # Intercalar dados para GPU
        interleaved = np.column_stack((positions, normals, tex_coords, bone_ids.astype(np.float32), weights))
        vertex_data = interleaved.flatten().astype(np.float32)

        return Mesh(vertex_data, index_data)

    def draw(self, shader):
        for mesh in self.meshes:
            mesh.draw(shader)