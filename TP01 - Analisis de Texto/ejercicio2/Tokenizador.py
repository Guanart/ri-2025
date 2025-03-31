#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import json
import sys

class Tokenizador:
    def __init__(self, stopwords_path=None, eliminar_stopwords=False, min_len=1, max_len=20):
        self.stopwords = set()
        self.eliminar_stopwords = eliminar_stopwords
        self.min_len = min_len
        self.max_len = max_len

        if stopwords_path:
            with open(stopwords_path, "r") as f:
                for line in f:
                    self.stopwords.add(line.strip().lower())

    def tokenizar(self, texto):
        texto = re.sub(r"[^\w\s]|_", "", texto)
        tokens = texto.split()
        tokens = [token for token in tokens if token]   # Eliminar tokens vacios (cadenas vacias)
        tokens = [token.lower() for token in tokens if self.min_len <= len(token) <= self.max_len]
        if self.eliminar_stopwords:
            tokens = [token for token in tokens if token not in self.stopwords]
        return tokens

    def analizar_coleccion(self, path_documentos) -> dict:
        docs_analizados = 0
        cantidad_tokens = 0
        terminos = (
            {}
        )  # Almacena los terminos como keys, y como values los docid, freqs y DF
        tokens_terms_por_documento = {}   # Almacena los nombres de documentos como key y la cantidad de tokens y terminos como value

        for doc_name in os.listdir(path_documentos):
            path_doc = os.path.join(path_documentos, doc_name)
            with open(path_doc, "r") as f:
                texto = (
                    f.read()
                )  # Podemos leer los archivos completos, ya que no son muy grandes y solo tienen una linea
                tokens = self.tokenizar(texto)
                cantidad_tokens += len(tokens)

                # Ordenar tokens para aplicar corte de control
                tokens.sort()
                i = 0
                while i < len(tokens):
                    current = tokens[i]
                    count = 1
                    j = i + 1
                    while j < len(tokens) and tokens[j] == current:
                        count += 1
                        j += 1
                    if current not in terminos:
                        terminos[current] = {"docid": [], "freq": [], "df": 0}
                    # terminos[current]["docid"].append(doc_id)
                    # terminos[current]["freq"].append(count)
                    terminos[current]["df"] += 1

                    if doc_name not in tokens_terms_por_documento:
                        tokens_terms_por_documento[doc_name] = {"tokens": 0, "terminos": 0}
                    tokens_terms_por_documento[doc_name]["tokens"] += count
                    tokens_terms_por_documento[doc_name]["terminos"] += 1

                    i = j

                docs_analizados += 1

        # num_terminos = len(terminos)
        # promedio_tokens = sum(tokens_por_documento) / docs_analizados
        # promedio_terminos = sum(terminos_por_documento) / docs_analizados
        # largo_promedio_termino = sum(len(t) for t in terminos.keys()) / num_terminos
        # tokens_min = min(tokens_por_documento)
        # tokens_max = max(tokens_por_documento)
        # terminos_min = min(terminos_por_documento)
        # terminos_max = max(terminos_por_documento)
        # terminos_una_vez = sum(1 for t in terminos.values() if t["cf"] == 1)

        return {
            "terminos": terminos,
            "estadisticas": {
                "docs_analizados": docs_analizados,
                "cantidad_tokens": cantidad_tokens,
                # "num_terminos": num_terminos,
                # "promedio_tokens": promedio_tokens,
                # "promedio_terminos": promedio_terminos,
                # "largo_promedio_termino": largo_promedio_termino,
                # "tokens_min": tokens_min,
                # "tokens_max": tokens_max,
                # "terminos_min": terminos_min,
                # "terminos_max": terminos_max,
                # "terminos_una_vez": terminos_una_vez,
            },
        }

    def generar_archivos_salida(self, resultados, output_dir):
        terminos = resultados["terminos"]
        estadisticas = resultados["estadisticas"]

        # Archivo terminos.txt
        with open(os.path.join(output_dir, "terminos.txt"), "w") as f:
            for termino, data in sorted(terminos.items()):
                f.write(f"{termino} {data['cf']} {data['df']}\n")

        # Archivo estadisticas.txt
        with open(os.path.join(output_dir, "estadisticas.txt"), "w") as f:
            f.write(f"{estadisticas['docs_analizados']}\n")
            f.write(f"{estadisticas['cantidad_tokens']} {estadisticas['num_terminos']}\n")
            f.write(f"{estadisticas['promedio_tokens']} {estadisticas['promedio_terminos']}\n")
            f.write(f"{estadisticas['largo_promedio_termino']}\n")
            f.write(f"{estadisticas['tokens_min']} {estadisticas['tokens_max']}\n")
            f.write(f"{estadisticas['terminos_min']} {estadisticas['terminos_max']}\n")
            f.write(f"{estadisticas['terminos_una_vez']}\n")

        # Archivo frecuencias.txt
        with open(os.path.join(output_dir, "frecuencias.txt"), "w") as f:
            terminos_ordenados = sorted(terminos.items(), key=lambda x: x[1]["cf"], reverse=True)
            f.write("10 términos más frecuentes:\n")
            for termino, data in terminos_ordenados[:10]:
                f.write(f"{termino} {data['cf']}\n")
            f.write("\n10 términos menos frecuentes:\n")
            for termino, data in terminos_ordenados[-10:]:
                f.write(f"{termino} {data['cf']}\n")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Uso: python3 Tokenizador.py <directorio_documentos> <eliminar_stopwords> <archivo_stopwords> <directorio_salida>")
        sys.exit(1)

    path_documentos = sys.argv[1]
    eliminar_stopwords = sys.argv[2].lower() == "true"
    stopwords_path = sys.argv[3] if eliminar_stopwords else None
    output_dir = sys.argv[4]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tokenizador = Tokenizador(stopwords_path=stopwords_path, eliminar_stopwords=eliminar_stopwords)
    resultados = tokenizador.analizar_coleccion(path_documentos)
    tokenizador.generar_archivos_salida(resultados, output_dir)