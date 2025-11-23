#version 330 core

out vec4 out_color;

in vec3 v_normal;
in vec3 v_world_pos;
in vec4 v_frag_pos_light_space;

// Uniforms existentes no teu projeto
uniform vec3 u_sun_direction;
uniform vec3 u_sun_color;
uniform vec3 u_ambient_color;
uniform sampler2D u_shadow_map;
uniform vec3 u_sky_color; // <--- ADICIONE ISTO

// Configuração de Cores Sólidas (Estilo Messenger)
vec3 COLOR_GRASS = vec3(0.35, 0.75, 0.35); // Verde vivo
vec3 COLOR_CLIFF = vec3(0.4, 0.3, 0.2);    // Marrom terra
vec3 COLOR_WATER = vec3(0.1, 0.4, 0.8);    // Azul fundo (caso o mapa suba)

// Função de Sombra (Mantendo a tua lógica, apenas simplificando o uso)
float calculate_shadow(vec4 frag_pos_light_space, vec3 normal, vec3 light_dir)
{
    vec3 proj_coords = frag_pos_light_space.xyz / frag_pos_light_space.w;
    proj_coords = proj_coords * 0.5 + 0.5;
    
    // Se estiver fora do alcance do mapa de sombra
    if(proj_coords.z > 1.0) return 0.0;

    float current_depth = proj_coords.z;
    
    // Bias para evitar acne de sombra
    float bias = max(0.005 * (1.0 - dot(normal, light_dir)), 0.0005);
    
    // PCF simples (suaviza levemente as bordas)
    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(u_shadow_map, 0);
    for(int x = -1; x <= 1; ++x)
    {
        for(int y = -1; y <= 1; ++y)
        {
            float pcfDepth = texture(u_shadow_map, proj_coords.xy + vec2(x, y) * texelSize).r; 
            shadow += current_depth - bias > pcfDepth ? 1.0 : 0.0;        
        }    
    }
    shadow /= 9.0;
    
    return shadow;
}

void main()
{
    // 1. Configuração Básica
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_sun_direction);
    
    // 2. Definir a Cor do Objeto baseada na inclinação (Sem texturas)
    // Se a normal aponta pra cima (> 0.8), é grama. Se é lado, é pedra.
    float slope = smoothstep(0.6, 0.8, N.y);
    vec3 object_color = mix(COLOR_CLIFF, COLOR_GRASS, slope);
    
    // Se a altura for muito baixa (perto do mar/vazio), escurece ou muda cor
    if (v_world_pos.y < 2.0) object_color = mix(COLOR_CLIFF, COLOR_WATER, 0.5);

    // 3. Iluminação Toon (Cel Shading)
    float diff = max(dot(N, L), 0.0);
    
    // Quantização da luz (Bandas de cor)
    float light_intensity;
    if (diff > 0.95) light_intensity = 1.0;
    else if (diff > 0.5) light_intensity = 0.7;
    else if (diff > 0.2) light_intensity = 0.3;
    else light_intensity = 0.1; // Sombra própria do objeto

    // 4. Sombras Projetadas (Shadow Map)
    float shadow = calculate_shadow(v_frag_pos_light_space, N, L);
    
    // A sombra força a intensidade para o nível mais baixo
    vec3 lighting = u_ambient_color + (u_sun_color * light_intensity * (1.0 - shadow));
    
    // 5. Cor Final
    vec3 final_rgb = object_color * lighting;
    
    // Opcional: Névoa simples integrada para esconder o fim do mundo
    // (A cor da névoa deveria combinar com o céu, aqui pus um azul genérico)
    float dist = length(v_world_pos.xz); // Distância do centro (0,0)
    float fog = smoothstep(280.0, 450.0, dist); // Começa em 280m, total em 450m

    // Mistura com a cor do "fundo" (Skybox color seria ideal aqui)
    final_rgb = mix(final_rgb, u_sky_color, fog);

    out_color = vec4(final_rgb, 1.0);
}