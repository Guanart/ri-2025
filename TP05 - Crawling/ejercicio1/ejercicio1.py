import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Crawler import Crawler
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Descarga una página HTML y muestra sus enlaces."
    )
    parser.add_argument(
        "url", help="URL de la página a descargar. Debe comenzar con http:// o https://"
    )
    parser.add_argument(
        "--preserve-query", 
        action="store_true", 
        help="Preservar query strings en las URLs (por defecto: False)"
    )
    args = parser.parse_args()
    url = args.url
    preserve_query = args.preserve_query

    print(f"Configuración: preserve_query={preserve_query}")
    
    crawler = Crawler(
        max_depth=0, max_dir_depth=0, max_pages_per_site=1, preserve_query=preserve_query
    )

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
