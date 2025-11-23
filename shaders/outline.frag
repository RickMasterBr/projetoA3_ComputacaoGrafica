#version 330 core
out vec4 out_color;
uniform vec3 u_sky_color; // Para o fog afetar a linha também

void main() {
    out_color = vec4(0.1, 0.1, 0.15, 1.0); // Preto levemente azulado
}