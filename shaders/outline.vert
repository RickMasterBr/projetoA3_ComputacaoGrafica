#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 2) in vec3 aNormal; // Precisa das normais para expandir

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform float u_thickness; // Espessura da linha (ex: 0.05)

void main() {
    // Expande o vértice na direção da normal
    vec3 pos = aPos + aNormal * u_thickness;
    gl_Position = projection * view * model * vec4(pos, 1.0);
}