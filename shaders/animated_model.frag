#version 410 core

out vec4 FragColor;

in vec3 v_frag_pos;
in vec3 v_normal;
in vec2 v_tex_coords;
in vec4 v_frag_pos_light_space;

uniform vec3 u_sun_direction;
uniform vec3 u_sun_color;
uniform vec3 u_ambient_color;
uniform sampler2D u_shadow_map;
uniform vec3 u_sky_color;  // COR DO CÉU PARA FOG

// Textura enviada pelo Python
uniform sampler2D u_texture_diffuse;
uniform int u_has_texture; // 1 = Sim, 0 = Não

float calculate_shadow(vec4 frag_pos_light_space, vec3 N, vec3 L) {
    vec3 proj_coords = frag_pos_light_space.xyz / frag_pos_light_space.w;
    proj_coords = proj_coords * 0.5 + 0.5;
    if(proj_coords.z > 1.0) return 0.0;
    float closest_depth = texture(u_shadow_map, proj_coords.xy).r; 
    float current_depth = proj_coords.z;
    float bias = max(0.005 * (1.0 - dot(N, L)), 0.001);
    return current_depth - bias > closest_depth ? 1.0 : 0.0;
}

void main()
{
    // 1. COR DO BONECO (Textura ou Cor Padrão)
    vec4 objectColor;
    if (u_has_texture == 1) {
        objectColor = texture(u_texture_diffuse, v_tex_coords);
    } else {
        objectColor = vec4(0.7, 0.7, 0.7, 1.0); // Cinza padrão se falhar a imagem
    }
    
    // Alpha Clipping (Transparência)
    if(objectColor.a < 0.1) discard;

    // 2. ILUMINAÇÃO
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_sun_direction);
    float diff = max(dot(N, L), 0.0);
    float shadow = calculate_shadow(v_frag_pos_light_space, N, L);
    
    vec3 ambient = u_ambient_color * objectColor.rgb;
    vec3 diffuse = diff * u_sun_color * objectColor.rgb;

    // Cor final antes do Fog
    vec3 finalColor = ambient + (1.0 - shadow) * diffuse;

    // 3. APLICAÇÃO DO FOG
    float depth = gl_FragCoord.z / gl_FragCoord.w;
    float fog_factor = smoothstep(200.0, 450.0, depth);
    
    // Mistura a cor final com a cor do céu baseada na distância
    vec3 color_with_fog = mix(finalColor, u_sky_color, fog_factor);

    // 4. SAÍDA FINAL
    FragColor = vec4(color_with_fog, 1.0);
}