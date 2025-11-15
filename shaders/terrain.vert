#version 410 core

layout (location = 0) in vec3 in_position;

// Matrizes para transformar o 3D em 2D na tela
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    // Multiplica: Projeção * Visão * Modelo * Posição
    gl_Position = projection * view * model * vec4(in_position, 1.0);
}