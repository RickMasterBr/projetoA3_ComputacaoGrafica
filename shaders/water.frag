#version 330 core
out vec4 FragColor;

in vec3 v_pos;

uniform vec3 u_color;
uniform vec3 u_sky_color;

void main()
{
    // Fog simples para a água se misturar com o horizonte
    float dist = length(v_pos.xz);
    float fog = smoothstep(300.0, 500.0, dist);
    
    vec3 final_rgb = mix(u_color, u_sky_color, fog);
    
    // Alpha 0.8 para ser meio transparente
    FragColor = vec4(final_rgb, 0.85);
}