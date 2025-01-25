import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont

def add_watermark(image_path):
    # Abrir a imagem
    img = Image.open(image_path)
    
    # Criar objeto de desenho
    draw = ImageDraw.Draw(img)
    
    # Configurar a fonte (usando fonte padrão)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Texto da marca d'água
    watermark_text = "Desenvolvido por: Igor Soares (manfullwel)"
    
    # Obter tamanho do texto
    text_width = draw.textlength(watermark_text, font=font)
    
    # Posição do texto (canto inferior direito)
    x = img.width - text_width - 20
    y = img.height - 50
    
    # Adicionar sombra para melhor legibilidade
    shadow_offset = 2
    draw.text((x + shadow_offset, y + shadow_offset), watermark_text, font=font, fill='black')
    draw.text((x, y), watermark_text, font=font, fill='white')
    
    # Salvar imagem
    img.save(image_path, quality=85, optimize=True)

def setup_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def capture_dashboard(url, output_dir):
    driver = setup_chrome_driver()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Navigate to dashboard
        driver.get(url)
        time.sleep(5)  # Wait for dashboard to load
        
        # Take screenshot
        filename = f"dashboard_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        driver.save_screenshot(filepath)
        
        # Adicionar marca d'água
        add_watermark(filepath)
        
        print(f"Screenshot saved: {filename}")
        return True
    except Exception as e:
        print(f"Error capturing screenshot: {str(e)}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    dashboard_url = "http://localhost:8052"
    output_dir = os.path.join("docs", "screenshots")
    capture_dashboard(dashboard_url, output_dir)
