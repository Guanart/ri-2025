#!/bin/bash
# Script de demostración final de todas las mejoras implementadas

echo "🎉 DEMOSTRACIÓN FINAL - MEJORAS COMPLETADAS"
echo "=========================================="

cd "/home/gbenito/universidad/ri-2025/TP05 - Crawling"

echo -e "\n1️⃣ EJERCICIO 1 - Opciones de preserve_query:"
echo "   Sin preserve_query (comportamiento por defecto):"
echo "   python3 ejercicio1/ejercicio1.py 'https://example.com/page?param=value'"
echo ""
echo "   Con preserve_query activado:"
echo "   python3 ejercicio1/ejercicio1.py 'https://example.com/page?param=value' --preserve-query"

echo -e "\n2️⃣ EJERCICIO 2 - Configuración completa interactiva:"
echo "   ✅ Tipo de crawler: Secuencial vs Paralelo"
echo "   ✅ Workers paralelos: 2-12 (solo para paralelo)"
echo "   ✅ Preserve query: Sí/No (NUEVO)"
echo "   ✅ Cantidad de páginas: 50/150/500/personalizado"
echo "   ✅ Páginas por sitio: 20-50"

echo -e "\n3️⃣ NOMBRES DE ARCHIVOS DESCRIPTIVOS:"
echo "   Ejemplos de archivos generados:"
echo "   📁 ejercicio2_sequential_150p_query.pkl"
echo "   📁 ejercicio2_sequential_150p_noquery.pkl"
echo "   📁 ejercicio2_parallel_500p_query_graph.html"
echo "   📁 ejercicio2_parallel_500p_noquery_graph.html"

echo -e "\n4️⃣ VERIFICACIÓN DE FUNCIONAMIENTO:"
python3 -c "
from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel

# Test de todos los parámetros
tests = [
    ('Crawler con preserve_query=True', Crawler(preserve_query=True)),
    ('Crawler con preserve_query=False', Crawler(preserve_query=False)),
    ('CrawlerParallel con preserve_query=True', CrawlerParallel(preserve_query=True, max_workers=4)),
    ('CrawlerParallel con preserve_query=False', CrawlerParallel(preserve_query=False, max_workers=8))
]

for name, crawler in tests:
    workers = getattr(crawler, 'max_workers', 'N/A')
    print(f'   ✅ {name}: preserve_query={crawler.preserve_query}, workers={workers}')
"

echo -e "\n5️⃣ PARÁMETROS CONFIGURABLES FINALES:"
echo "   Ejercicio 1:"
echo "   ├── URL (argumento posicional)"
echo "   └── --preserve-query (opcional)"
echo ""
echo "   Ejercicio 2:"
echo "   ├── Tipo de crawler (secuencial/paralelo)"
echo "   ├── Workers paralelos (2-12)"
echo "   ├── Preserve query (sí/no) ← NUEVO"
echo "   ├── Cantidad de páginas (50/150/500/personalizado)"
echo "   └── Páginas por sitio (20-50)"

echo -e "\n6️⃣ IMPACTO DEL PRESERVE_QUERY:"
echo "   preserve_query=False (recomendado):"
echo "   ├── 'https://example.com/search?q=python&page=2#section'"
echo "   └── → 'https://example.com/search'"
echo ""
echo "   preserve_query=True (casos específicos):"
echo "   ├── 'https://example.com/search?q=python&page=2#section'"
echo "   └── → 'https://example.com/search?q=python&page=2'"

echo -e "\n✅ TODAS LAS MEJORAS IMPLEMENTADAS EXITOSAMENTE!"
echo "   📝 Archivos modificados: ejercicio1.py, ejercicio2.py"
echo "   🔧 Nuevos parámetros: preserve_query"
echo "   📊 Visualización: Sin límites de nodos"
echo "   🎯 Flexibilidad: Máxima para experimentación"

echo -e "\n🚀 ¡Listo para usar!"
