#!/bin/bash
# Test automático del ejercicio 2 parametrizado

echo "=== TEST EJERCICIO 2 PARAMETRIZADO ==="

# Test 1: Crawler secuencial con 50 páginas
echo -e "n\n1" | python3 ejercicio2/ejercicio2.py

echo -e "\n=== ARCHIVOS GENERADOS ==="
ls -la ejercicio2/*.pkl ejercicio2/*.html 2>/dev/null || echo "No hay archivos generados aún"

echo -e "\n=== TEST COMPLETADO ==="
