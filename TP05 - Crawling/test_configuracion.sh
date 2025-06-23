#!/bin/bash
# Test ejercicio 2 con configuración personalizada

echo "=== TEST CONFIGURACIÓN PERSONALIZADA ==="

# Test: Crawler secuencial, 100 páginas, 50 páginas por sitio
echo "Probando: secuencial + 100 páginas + 50 por sitio"
echo -e "n\n4\n100\n2" | python3 ejercicio2/ejercicio2.py

echo -e "\n=== ARCHIVOS GENERADOS ==="
ls -la ejercicio2/*100p* 2>/dev/null || echo "No hay archivos con 100p generados"

echo -e "\n=== TEST COMPLETADO ==="
