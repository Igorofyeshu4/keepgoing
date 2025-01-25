import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def criar_mockup_dashboard():
    # Criar imagem
    width = 1242
    height = 2688
    img = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Desenhar header
    draw.rectangle([0, 0, width, 200], fill='#2c3e50')
    draw.text((width//2, 100), 'Análise de Demandas', fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 40))
    
    # Status Card
    draw.rounded_rectangle([50, 250, width-50, 400], radius=20, fill='#34495e')
    draw.text((100, 300), '✅ Resolvidos Hoje: 270', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    draw.text((100, 350), '📊 Taxa de Resolução: 85%', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    
    # Equipe Julio Card
    draw.rounded_rectangle([50, 450, width-50, 700], radius=20, fill='#3498db')
    draw.text((100, 500), 'Equipe Julio', fill='white', font=ImageFont.truetype('arial.ttf', 35))
    draw.text((100, 550), 'Resolvidos: 140', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    draw.text((100, 600), 'Pendentes: 102', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    
    # Equipe Leandro/Adriano Card
    draw.rounded_rectangle([50, 750, width-50, 1000], radius=20, fill='#9b59b6')
    draw.text((100, 800), 'Equipe Leandro/Adriano', fill='white', font=ImageFont.truetype('arial.ttf', 35))
    draw.text((100, 850), 'Resolvidos: 130', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    draw.text((100, 900), 'Pendentes: 161', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    
    # Menu inferior
    draw.rectangle([0, height-100, width, height], fill='#2c3e50')
    icons = ['📊', '📈', '👥', '⚙️']
    labels = ['Dashboard', 'Gráficos', 'Equipes', 'Config']
    for i, (icon, label) in enumerate(zip(icons, labels)):
        x = width * (i + 1) / (len(icons) + 1)
        draw.text((x, height-70), icon, fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 30))
        draw.text((x, height-30), label, fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 20))
    
    return img

def criar_mockup_graficos():
    # Criar imagem
    width = 1242
    height = 2688
    img = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.rectangle([0, 0, width, 200], fill='#2c3e50')
    draw.text((width//2, 100), 'Gráficos', fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 40))
    
    # Gráfico de Pizza
    draw.rounded_rectangle([50, 250, width-50, 600], radius=20, fill='#34495e')
    draw.text((100, 300), 'Distribuição de Demandas', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    
    # Gráfico de Barras
    draw.rounded_rectangle([50, 650, width-50, 1000], radius=20, fill='#34495e')
    draw.text((100, 700), 'Comparativo entre Equipes', fill='white', font=ImageFont.truetype('arial.ttf', 30))
    
    # Menu inferior
    draw.rectangle([0, height-100, width, height], fill='#2c3e50')
    icons = ['📊', '📈', '👥', '⚙️']
    labels = ['Dashboard', 'Gráficos', 'Equipes', 'Config']
    for i, (icon, label) in enumerate(zip(icons, labels)):
        x = width * (i + 1) / (len(icons) + 1)
        draw.text((x, height-70), icon, fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 30))
        draw.text((x, height-30), label, fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 20))
    
    return img

def criar_mockup_equipes():
    # Criar imagem
    width = 1242
    height = 2688
    img = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.rectangle([0, 0, width, 200], fill='#2c3e50')
    draw.text((width//2, 100), 'Equipes', fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 40))
    
    # Lista de membros
    equipes = [
        ('Equipe Julio', ['João', 'Maria', 'Pedro']),
        ('Equipe Leandro/Adriano', ['Ana', 'Carlos', 'Paulo'])
    ]
    
    y = 250
    for equipe, membros in equipes:
        draw.rounded_rectangle([50, y, width-50, y+250], radius=20, fill='#34495e')
        draw.text((100, y+50), equipe, fill='white', font=ImageFont.truetype('arial.ttf', 35))
        for i, membro in enumerate(membros):
            draw.text((100, y+100+i*40), f'• {membro}', fill='white', font=ImageFont.truetype('arial.ttf', 30))
        y += 300
    
    # Menu inferior
    draw.rectangle([0, height-100, width, height], fill='#2c3e50')
    icons = ['📊', '📈', '👥', '⚙️']
    labels = ['Dashboard', 'Gráficos', 'Equipes', 'Config']
    for i, (icon, label) in enumerate(zip(icons, labels)):
        x = width * (i + 1) / (len(icons) + 1)
        draw.text((x, height-70), icon, fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 30))
        draw.text((x, height-30), label, fill='white', anchor='mm', font=ImageFont.truetype('arial.ttf', 20))
    
    return img

if __name__ == "__main__":
    # Criar diretório se não existir
    output_dir = 'docs/images/mobile'
    os.makedirs(output_dir, exist_ok=True)
    
    # Gerar mockups
    print("Gerando mockups das telas mobile...")
    
    dashboard = criar_mockup_dashboard()
    dashboard.save(os.path.join(output_dir, 'dashboard.png'))
    
    graficos = criar_mockup_graficos()
    graficos.save(os.path.join(output_dir, 'charts.png'))
    
    equipes = criar_mockup_equipes()
    equipes.save(os.path.join(output_dir, 'team.png'))
    
    print("Mockups gerados com sucesso!")
