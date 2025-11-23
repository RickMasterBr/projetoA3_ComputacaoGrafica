#version 330 core
out vec4 out_color;

in vec3 v_normal;
in vec3 v_color;

uniform vec3 u_sun_direction;
uniform vec3 u_sun_color;
uniform vec3 u_ambient_color;
uniform vec3 u_sky_color; // <--- NOVO

void main()
{
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_sun_direction);
    
    // Iluminação Toon Simples
    float diff = max(dot(N, L), 0.0);
    float light_intensity;
    
    if (diff > 0.8) light_intensity = 1.0;
    else if (diff > 0.4) light_intensity = 0.6;
    else light_intensity = 0.3; // Sombra

    vec3 light = u_ambient_color + (u_sun_color * light_intensity);

    vec3 color_result = v_color * light;

    // Calculo simples de Fog baseado na profundidade do fragmento
    float depth = gl_FragCoord.z / gl_FragCoord.w; 
    float fog_factor = smoothstep(80.0, 280.0, depth);
    
    out_color = vec4(mix(color_result, u_sky_color, fog_factor), 1.0);
}