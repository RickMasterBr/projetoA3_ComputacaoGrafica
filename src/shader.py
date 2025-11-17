from OpenGL.GL import *
import ctypes
import glm

class Shader:
    def __init__ (self, vertex_path, fragment_path):

        # Carregar o código fonte dos shaders
        try:
            with open(vertex_path, 'r', encoding='utf-8') as f:
                vertex_source = f.read()
            with open(fragment_path, 'r', encoding='utf-8') as f:
                fragment_source = f.read()
        except FileNotFoundError as e:
            print("Erro: Arquivo de shader não encontrado. {e}")
            raise

        # Compilar os Shaders
        vertex_shader = self._compile_shader(vertex_source, GL_VERTEX_SHADER)
        fragment_shader = self._compile_shader(fragment_source, GL_FRAGMENT_SHADER)

        # Linkar shaders em um programa
        self.program_id = self._link_program(vertex_shader, fragment_shader)

        # excluir os shaders individuais, pois já estão no programa
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def _compile_shader(self, source, shader_type):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        # Verificar erros de compilação
        success = glGetShaderiv(shader, GL_COMPILE_STATUS)
        if not success:
            info_log = glGetShaderInfoLog(shader).decode('utf-8')
            print(f"Erro de compilação do {shader_type}:\n{info_log}")
            raise RuntimeError("Falha na compilação do shader.")
        return shader
    
    def _link_program(self, vertex_shader, fragment_shader):
        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)

        # Verificar erros de linkagem
        success = glGetProgramiv(program, GL_LINK_STATUS)
        if not success:
            info_log = glGetProgramInfoLog(program).decode('utf-8')
            print(f"Erro de linkagem do programa:\n{info_log}")
            raise RuntimeError("Falha na linkagem do programa.")
        return program
    
    def use(self):
        """Ativa o programa de shader."""
        glUseProgram(self.program_id)

    # Funções auxiliares para definir uniformes

    def get_uniform_location(self, name):
        # Cache de localizações (opcional, mas bom para performance)
        if not hasattr(self, '_uniform_cache'):
            self._uniform_cache = {}
        if name not in self._uniform_cache:
            self._uniform_cache[name] = glGetUniformLocation(self.program_id, name)
        return self._uniform_cache[name]

    def set_uniform_mat4(self, name, matrix):
        """Define um uniform do tipo mat4 (matriz 4x4)."""
        location = self.get_uniform_location(name)
        # O 'transpose' (GL_FALSE) indica que a matriz está no formato correto (column-major)
        glUniformMatrix4fv(location, 1, GL_FALSE, glm.value_ptr(matrix))

    def set_uniform_vec3(self, name, vector):
        """Define um uniform do tipo vec3 (vetor 3D)."""
        location = self.get_uniform_location(name)
        if isinstance(vector, glm.vec3):
             glUniform3fv(location, 1, glm.value_ptr(vector))
        else:
             glUniform3fv(location, 1, vector)

    def set_uniform_float(self, name, value):
        """Define um uniform do tipo float."""
        location = self.get_uniform_location(name)
        glUniform1f(location, value)

    def set_uniform_int(self, name, value):
        """Define um uniform do tipo int."""
        location = self.get_uniform_location(name)
        glUniform1i(location, value)
        