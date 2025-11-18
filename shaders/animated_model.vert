#version 410 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec2 in_tex_coords;
// --- NOVOS ATRIBUTOS ---
layout (location = 3) in ivec4 in_bone_ids;  // IDs dos ossos (inteiros)
layout (location = 4) in vec4 in_weights;    // Pesos (floats)

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 u_light_space_matrix;

out vec3 v_normal;
out vec2 v_tex_coords;
out vec4 v_frag_pos_light_space;

void main()
{
    // Por enquanto, ignoramos a animação e desenhamos estático
    // (O Módulo 6 - Parte 3 ativará isso)
    
    vec4 total_position = vec4(in_position, 1.0);
    
    vec4 world_pos = model * total_position;
    v_normal = mat3(model) * in_normal;
    v_tex_coords = in_tex_coords;
    
    v_frag_pos_light_space = u_light_space_matrix * world_pos;

    gl_Position = projection * view * world_pos;
}