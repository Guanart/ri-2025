# Mejoras Implementadas - Parámetro preserve_query

## Resumen de Cambios

Se ha agregado exitosamente el parámetro `preserve_query` a ambos ejercicios del TP05, completando así todas las mejoras solicitadas.

## Cambios Realizados

### Ejercicio 1 (ejercicio1.py)
- ✅ **Agregado parámetro `--preserve-query`**: Nuevo argumento opcional de línea de comandos
- ✅ **Valor por defecto**: `preserve_query=False` (comportamiento más común)
- ✅ **Configuración mostrada**: Se muestra la configuración antes de ejecutar el crawler

**Uso:**
```bash
# Sin preservar query strings (por defecto)
python3 ejercicio1.py "https://example.com/page?param=value"

# Preservando query strings
python3 ejercicio1.py "https://example.com/page?param=value" --preserve-query
```

### Ejercicio 2 (ejercicio2.py)
- ✅ **Input interactivo**: Nueva pregunta para elegir si preservar query strings
- ✅ **Configuración en crawlers**: Parámetro pasado tanto a `Crawler` como `CrawlerParallel`
- ✅ **Nombres de archivos**: Incluye `query` o `noquery` en los nombres de archivos de salida
- ✅ **Información mostrada**: Se muestra la configuración durante el crawling

**Nombres de archivos generados:**
- `ejercicio2_sequential_150p_query.pkl` (con preserve_query=True)
- `ejercicio2_sequential_150p_noquery.pkl` (con preserve_query=False)
- `ejercicio2_parallel_150p_query_graph.html` (con preserve_query=True)
- `ejercicio2_parallel_150p_noquery_graph.html` (con preserve_query=False)

## Parámetros Configurables Completos

### Ejercicio 1
1. **URL**: URL a analizar (argumento posicional)
2. **preserve_query**: Preservar query strings (--preserve-query)

### Ejercicio 2
1. **Tipo de crawler**: Secuencial o paralelo (input interactivo)
2. **Workers paralelos**: 2-12 workers (solo para crawler paralelo)
3. **preserve_query**: Preservar query strings (input interactivo)
4. **Cantidad de páginas**: 50, 150, 500 o personalizado
5. **Páginas por sitio**: 20-50 páginas por dominio

## Impacto del Parámetro preserve_query

### preserve_query=False (Recomendado por defecto)
- **Ventajas**: Menos URLs duplicadas, crawling más eficiente
- **Comportamiento**: Elimina query strings y fragments de las URLs
- **Uso típico**: Crawling general, análisis de estructura de sitios

**Ejemplo:**
- URL original: `https://example.com/search?q=python&page=2#results`
- URL procesada: `https://example.com/search`

### preserve_query=True (Para casos específicos)
- **Ventajas**: Mantiene contexto de páginas dinámicas específicas
- **Comportamiento**: Preserva query strings, solo elimina fragments
- **Uso típico**: Análisis de páginas de búsqueda, APIs, páginas paramétricas

**Ejemplo:**
- URL original: `https://example.com/search?q=python&page=2#results`
- URL procesada: `https://example.com/search?q=python&page=2`

## Verificación de Funcionamiento

### Tests Implementados
1. **test_preserve_query_quick.sh**: Script de prueba rápida
2. **test_preserve_query.py**: Test completo comparativo existente

### Verificación Manual
```bash
# Test básico de funcionamiento
cd /home/gbenito/universidad/ri-2025/TP05\ -\ Crawling
python3 -c "
from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel
c1 = Crawler(preserve_query=True)
c2 = CrawlerParallel(preserve_query=False)
print('✅ Tests básicos OK')
"
```

## Estado Final

### ✅ Completado
- [x] Elegir entre Crawler secuencial y paralelo (ejercicio 2)
- [x] Configurar cantidad de páginas totales
- [x] Configurar páginas por sitio  
- [x] Configurar cantidad de workers (crawler paralelo)
- [x] **Configurar preserve_query (NUEVO)**
- [x] Mostrar todos los nodos en visualización
- [x] Nombres de archivos descriptivos
- [x] Scripts claros y flexibles para experimentación

### Archivos Modificados
- `ejercicio1/ejercicio1.py`: Agregado parámetro --preserve-query
- `ejercicio2/ejercicio2.py`: Agregado input interactivo y configuración completa
- `test_preserve_query_quick.sh`: Script de verificación (NUEVO)

### Archivos de Salida Mejorados
Los nombres de archivos ahora incluyen toda la configuración:
- Tipo de crawler: `sequential` o `parallel`
- Cantidad de páginas: `150p`, `500p`, etc.
- Query handling: `query` o `noquery`

**Ejemplo**: `ejercicio2_parallel_500p_noquery_graph.html`

## Recomendaciones de Uso

1. **Para crawling general**: `preserve_query=False` (más eficiente)
2. **Para análisis de búsquedas**: `preserve_query=True` (más detallado)
3. **Para comparaciones**: Ejecutar ambas versiones y comparar resultados
4. **Para experimentación**: Usar nombres de archivos descriptivos para organizar experimentos

¡Todas las mejoras solicitadas han sido implementadas exitosamente! 🎉
