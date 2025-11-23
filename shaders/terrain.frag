#version 330 core

out vec4 out_color;

in vec3 v_normal;
in vec3 v_world_pos;
in vec4 v_frag_pos_light_space;

uniform vec3 u_sun_direction;
uniform vec3 u_sun_color;     // Cor do Sol (Luz)
uniform vec3 u_ambient_color; // Cor da Sombra
uniform vec3 u_sky_color;     // Cor do Céu (para o Fog)
uniform sampler2D u_shadow_map;

// --- PALETA MESSENGER (Hardcoded para garantir o estilo) ---
const vec3 COLOR_LIGHT  = vec3(0.48, 0.77, 0.63); // Verde Menta (Topo)
const vec3 COLOR_SHADOW = vec3(0.25, 0.28, 0.40); // Azulacinzentado (Lados)
const vec3 RIM_COLOR    = vec3(1.0, 1.0, 0.9);    // Borda Brilhante

float calculate_shadow(vec4 frag_pos_light_space, vec3 N, vec3 L) {
    vec3 proj_coords = frag_pos_light_space.xyz / frag_pos_light_space.w;
    proj_coords = proj_coords * 0.5 + 0.5;
    if(proj_coords.z > 1.0) return 0.0;
    
    // PCF Suave (4 samples)
    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(u_shadow_map, 0);
    for(int x = -1; x <= 0; ++x) {
        for(int y = -1; y <= 0; ++y) {
            float pcfDepth = texture(u_shadow_map, proj_coords.xy + vec2(x, y) * texelSize).r; 
            shadow += proj_coords.z - 0.005 > pcfDepth ? 1.0 : 0.0;        
        }    
    }
    return shadow / 4.0;
}

void main() {
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_sun_direction);
    vec3 V = normalize(vec3(0.0, 5.0, 0.0) - v_world_pos); // View dir aproximada

    // 1. Toon Ramp (5 Níveis Suaves)
    float NdotL = dot(N, L);
    float light_intensity = smoothstep(-0.1, 0.1, NdotL) * 0.6 + 
                            smoothstep(0.4, 0.6, NdotL) * 0.3 + 0.1;

    // 2. Sombras
    float shadow = calculate_shadow(v_frag_pos_light_space, N, L);
    float final_light = light_intensity * (1.0 - shadow * 0.5); // Sombra não é 100% preta

    // 3. Cor Base (Gradiente Vertical Suave)
    float height_factor = smoothstep(5.0, 40.0, v_world_pos.y);
    vec3 terrain_color = mix(COLOR_SHADOW, COLOR_LIGHT, height_factor);

    // 4. Rim Light (Luz de Borda)
    float rim = 1.0 - max(dot(N, V), 0.0);
    rim = smoothstep(0.6, 1.0, rim) * 0.3;

    vec3 final_rgb = terrain_color * (u_ambient_color * 0.5 + final_light) + (RIM_COLOR * rim);

    // 5. Fog Artístico (Mistura com o Céu)
    float dist = length(v_world_pos.xz);
    float fog = smoothstep(80.0, 280.0, dist);
    final_rgb = mix(final_rgb, u_sky_color, fog);

    out_color = vec4(final_rgb, 1.0);
}