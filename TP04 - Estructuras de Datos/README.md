# TP04 - Estructuras de Datos
## Ejercicio 1
Se incluye un script ejercicio1/ejercicio1.py donde se puede consultar la posting list de un término. Además, se incluye en la raíz una notebook ejercicio1.ipynb con los gráficos y comparaciones.
```bash
#  Ejecutar desde la raíz del TP (ejemplo con documentos en directorio /datos)
python3 -m ejercicio1.ejercicio1 --corpus-path datos/en/articles --termino president
```
## Ejercicio 2
```bash
#  Ejecutar desde la raíz del TP (ejemplo con documentos en directorio /datos)
python3 -m ejercicio2.ejercicio2 --corpus-path datos/en/articles --query '(perro AND gato) OR raton'
```
## Ejercicio 3
```bash
#  Ejecutar desde la raíz del TP (ejemplo con documentos en directorio /datos)
python3 -m ejercicio3.ejercicio3 --corpus-path datos/articles --queries-file queries/EFF-10K-queries.txt
```
## Ejercicio 4
```bash
#  Ejecutar desde la raíz del TP (ejemplo con documentos en directorio /datos)
python3 -m ejercicio4.ejercicio4 --corpus-path datos/articles --query 'president usa' --top-k 10
```
## Ejercicio 5
```bash
#  Ejecutar desde la raíz del TP (ejemplo con documentos en directorio /datos)
python3 -m ejercicio5.ejercicio5 --corpus-path datos/en/articles --queries-file EFF-10K-queries.txt
python3 -m ejercicio5.ejercicio5_1 --corpus-path datos/en/articles --termino president
```
## Ejercicio 6
```bash
#  Ejecutar desde la raíz del TP
python3 -m ejercicio6.ejercicio6 --corpus-path dump10k.txt --queries-file queriesDump10K.txt --top-k 10
```
## Ejercicio 7
```bash
#  Ejecutar desde la raíz del TP
python ejercicio7.py --index-dir index --dgaps
python ejercicio7_1.py --index-dir index --termino TU_TERMINO --dgaps
```