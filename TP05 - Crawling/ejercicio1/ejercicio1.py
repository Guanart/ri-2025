from lib.Crawler import Crawler
import argparse

def main():
    parser = argparse.ArgumentParser(description="Descarga una página HTML y muestra sus enlaces.")
    parser.add_argument("url", help="URL de la página a descargar. Debe comenzar con http:// o https://")
    args = parser.parse_args()
    url = args.url
    
    crawler = Crawler(max_depth=0, max_dir_depth=0, max_pages_per_site=1, preserve_query=True)
    
    print(f"Descargando página: {url}")
    
    # Solo descargar la página y extraer enlaces
    page = crawler.fetch_page(url)
    if page:
        links = crawler.parse_links(page, url)
        print(f"\nEnlaces encontrados en {url}:")
        print(f"Total de enlaces: {len(links)}")
        print("-" * 50)
        for i, link in enumerate(links, 1):
            print(f"{i:3d}. {link}")
    else:
        print("❌ No se pudo descargar la página.")

if __name__ == "__main__":
    main()