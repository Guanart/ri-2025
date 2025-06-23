#!/bin/bash
# Script de prueba rápida para validar los cambios de preserve_query

echo "=== Test de preserve_query - Ejercicio 1 ==="
echo "1. Probando ejercicio1 SIN preserve_query (por defecto):"
cd "/home/gbenito/universidad/ri-2025/TP05 - Crawling/ejercicio1"
python3 ejercicio1.py "https://httpbin.org/get?test=1" | head -5

echo -e "\n2. Probando ejercicio1 CON preserve_query:"
python3 ejercicio1.py "https://httpbin.org/get?test=1" --preserve-query | head -5

echo -e "\n=== Test de preserve_query - Ejercicio 2 ==="
echo "3. Verificando que ejercicio2 tenga la opción preserve_query:"
cd "/home/gbenito/universidad/ri-2025/TP05 - Crawling/ejercicio2"
grep -n "preserve_query" ejercicio2.py

echo -e "\n4. Verificando que los nombres de archivos incluyan el parámetro:"
grep -n "query_suffix" ejercicio2.py

echo -e "\n=== Test de imports ==="
echo "5. Verificando que los imports funcionen:"
cd "/home/gbenito/universidad/ri-2025/TP05 - Crawling"
python3 -c "
import sys
import os
sys.path.append('.')
from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel

# Test básico de preserve_query
c1 = Crawler(preserve_query=True)
c2 = Crawler(preserve_query=False)
cp1 = CrawlerParallel(preserve_query=True)
cp2 = CrawlerParallel(preserve_query=False)

print(f'Crawler preserve_query=True: {c1.preserve_query}')
print(f'Crawler preserve_query=False: {c2.preserve_query}')
print(f'CrawlerParallel preserve_query=True: {cp1.preserve_query}')
print(f'CrawlerParallel preserve_query=False: {cp2.preserve_query}')
print('✅ Todos los tests básicos pasaron!')
"

echo -e "\n🎉 Test rápido completado!"
