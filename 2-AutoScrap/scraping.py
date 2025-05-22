from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def mostrar_producto(productos):
    print("---Producto Encontrado---")
    for idx, producto in enumerate(productos, 1):
        print(f"{idx}. {producto['Titulo']} - {producto['Precio']}")

def buscar_producto():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=chrome_options)

    while True:
        print("\n \x1b[33m Bienvenido a Mercado Libre Colombia 🛒 \x1b[0m")
        palabra = input(" 🔍 Buscar producto ( o 'salir'): ").strip().lower()

        if palabra == "salir":
            print("Saliendo de la busqueda...")
            break

        try:
            url_busqueda = f"https://listado.mercadolibre.com.co/{palabra}?sb=all_mercadolibre#D%5BA:{palabra}%5D"
            print(f" Buscando productos para: {palabra}")
            print(f" URL de busqueda: {url_busqueda}")

            driver.get(url_busqueda)
            time.sleep(3) 

            productos = []
            items = driver.find_elements(By.CSS_SELECTOR, "ol.ui-search-layout li.ui-search-layout__item")
            for item in items:
                if item.find_elements(By.CSS_SELECTOR, ".poly-component__ads-promotions"):
                    continue

                titulo_tag = item.find_elements(By.CSS_SELECTOR, "h3.poly-component__title-wrapper a")
                precio_tag = item.find_elements(By.CSS_SELECTOR, "div.poly-price__current span.andes-money-amount__fraction")

                if titulo_tag and precio_tag:
                    titulo = titulo_tag[0].text.strip()
                    precio = precio_tag[0].text.strip()
                    productos.append({'Titulo': titulo, 'Precio': precio})

                if len(productos) == 5:
                    break

            if productos:
                mostrar_producto(productos)
            else:
                print("No se encontraron productos.")

        except Exception as e:
            print(f"Error: {e}")

    driver.quit()

if __name__ == "__main__":
    buscar_producto()