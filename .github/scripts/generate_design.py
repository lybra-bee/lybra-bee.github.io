#!/usr/bin/env python3
import os
import requests
import random
import base64
from datetime import datetime

def generate_design_assets():
    """Генерация всех дизайн-элементов для сайта"""
    print("🎨 Запуск генерации дизайн-элементов...")
    
    # Создаем структуру папок
    create_design_folders()
    
    # Генерация элементов
    generate_backgrounds()
    generate_hero_elements()
    generate_icons()
    generate_patterns()
    generate_ui_elements()
    
    print("✅ Все дизайн-элементы сгенерированы!")

def create_design_folders():
    """Создает структуру папок для дизайна"""
    folders = [
        'static/images/design/hero',
        'static/images/design/patterns',
        'static/images/design/icons',
        'static/images/design/ui',
        'static/images/backgrounds'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"📁 Создана папка: {folder}")

def generate_backgrounds():
    """Генерация фоновых изображений"""
    print("\n🎨 Генерация фонов...")
    
    backgrounds = {
        "bg-dark": "Dark cosmic background with stars and nebulae, deep blue and purple colors, 4K, high resolution, no text",
        "bg-gradient-blue": "Smooth blue gradient background from dark blue to electric blue, minimalist, abstract, 1920x1080",
        "bg-particles": "Floating digital particles with blue glow, dark background, abstract tech style, 1920x1080",
        "bg-neural": "Neural network background with interconnected nodes and pathways, blue glow, dark background, 1920x1080"
    }
    
    for name, prompt in backgrounds.items():
        generate_stability_image(
            prompt=prompt,
            output_path=f"static/images/backgrounds/{name}.jpg",
            width=1920,
            height=1080
        )

def generate_hero_elements():
    """Генерация элементов для hero секции"""
    print("\n🎨 Генерация hero элементов...")
    
    hero_elements = {
        "hero-bg": "Futuristic AI brain with neural connections in digital space, blue and purple neon lights, cyberpunk style, epic composition, 1920x1080",
        "hero-particle": "Floating tech particle with energy glow, transparent background, PNG, blue neon, 512x512",
        "hero-gradient": "Blue to purple gradient overlay with light effects, transparent background, PNG, 1920x1080"
    }
    
    for name, prompt in hero_elements.items():
        generate_stability_image(
            prompt=prompt,
            output_path=f"static/images/design/hero/{name}.png",
            width=1920 if 'bg' in name else 512,
            height=1080 if 'bg' in name else 512
        )

def generate_icons():
    """Генерация иконок"""
    print("\n🎨 Генерация иконок...")
    
    icons = {
        "icon-ai": "AI brain icon, blue neon style, futuristic, glowing, simple design, transparent background, PNG, 256x256",
        "icon-network": "Neural network icon, connected nodes, blue glow, transparent background, vector style, 256x256",
        "icon-chip": "Computer chip icon, futuristic, circuit lines, blue glow, transparent PNG, 256x256",
        "icon-quantum": "Quantum computing icon, particles and waves, blue energy, transparent background, 256x256",
        "icon-robot": "Robot face icon, minimalist, blue neon outline, futuristic, transparent PNG, 256x256"
    }
    
    for name, prompt in icons.items():
        generate_stability_image(
            prompt=prompt,
            output_path=f"static/images/design/icons/{name}.png",
            width=256,
            height=256
        )

def generate_patterns():
    """Генерация текстур и паттернов"""
    print("\n🎨 Генерация паттернов...")
    
    patterns = {
        "pattern-neural": "Neural network pattern, interconnected nodes and pathways, blue on dark background, seamless texture, 1000x1000",
        "pattern-circuit": "Circuit board texture, electronic lines and components, blue glow, dark background, seamless, 1000x1000",
        "pattern-hexagon": "Hexagon grid pattern, futuristic, blue glow, transparent background, PNG, 1000x1000",
        "pattern-dots": "Digital dots pattern, floating particles with blue glow, dark background, seamless, 1000x1000"
    }
    
    for name, prompt in patterns.items():
        generate_stability_image(
            prompt=prompt,
            output_path=f"static/images/design/patterns/{name}.png",
            width=1000,
            height=1000
        )

def generate_ui_elements():
    """Генерация UI элементов"""
    print("\n🎨 Генерация UI элементов...")
    
    ui_elements = {
        "button-bg": "Futuristic button background, blue glass morphism effect, glowing edges, transparent corners, PNG, 300x100",
        "card-bg": "Modern card background with subtle tech pattern, blue tint, glass effect, 400x300",
        "nav-bg": "Navigation bar background, dark with blue accents, minimalist tech style, 1920x80",
        "gradient-overlay": "Blue to transparent gradient overlay, smooth transition, PNG, 1920x500"
    }
    
    for name, prompt in ui_elements.items():
        sizes = {
            "button-bg": (300, 100),
            "card-bg": (400, 300),
            "nav-bg": (1920, 80),
            "gradient-overlay": (1920, 500)
        }
        
        width, height = sizes[name]
        generate_stability_image(
            prompt=prompt,
            output_path=f"static/images/design/ui/{name}.png",
            width=width,
            height=height
        )

def generate_stability_image(prompt, output_path, width, height):
    """Генерация изображения через Stability AI"""
    stability_key = os.getenv('STABILITYAI_KEY')
    
    if not stability_key:
        print(f"❌ STABILITYAI_KEY не найден для {output_path}")
        return False
    
    try:
        # Разрешенные размеры для SDXL
        allowed_dimensions = [
            (1024, 1024), (1152, 896), (1216, 832), 
            (1344, 768), (1536, 640), (640, 1536),
            (768, 1344), (832, 1216), (896, 1152)
        ]
        
        # Используем запрошенный размер или ближайший разрешенный
        final_width, final_height = get_closest_dimension(width, height, allowed_dimensions)
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": 7,
            "height": final_height,
            "width": final_width,
            "samples": 1,
            "steps": 30,
            "style_preset": "digital-art"
        }
        
        print(f"   Генерация: {os.path.basename(output_path)} ({final_width}x{final_height})")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'artifacts' in data and data['artifacts']:
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                print(f"   ✅ Успешно: {output_path}")
                return True
        else:
            print(f"   ❌ Ошибка {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
    
    return False

def get_closest_dimension(width, height, allowed_dimensions):
    """Находит ближайший разрешенный размер"""
    closest = min(allowed_dimensions, key=lambda dim: abs(dim[0] - width) + abs(dim[1] - height))
    return closest

if __name__ == "__main__":
    # Проверяем наличие ключа
    if not os.getenv('STABILITYAI_KEY'):
        print("❌ STABILITYAI_KEY не найден в переменных окружения")
        print("💡 Добавьте в GitHub Secrets: STABILITYAI_KEY")
        exit(1)
    
    # Запускаем генерацию
    generate_design_assets()
