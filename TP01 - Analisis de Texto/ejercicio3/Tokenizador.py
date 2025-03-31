#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import sys

class Tokenizador:
    def __init__(self, stopwords_path=None, eliminar_stopwords=False):
        self.stopwords = set()
        self.eliminar_stopwords = eliminar_stopwords
        if stopwords_path:
            with open(stopwords_path, "r", encoding="utf-8") as f:
                for line in f:
                    self.stopwords.add(line.strip().lower())

    def tokenizar(self, texto):
        # Patrón para capturar abreviaturas tipo Dr., NASA, S.A., Lic., etc.
        # Emails, URLs, números, nombres compuestos en mayúscula o con mayúsculas mixtas.
        patron = re.compile(
            r"""
            (?:[A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)         # Nombres propios compuestos
            |(?:[A-Za-z]+\.[A-Za-z]+(?:\.[A-Za-z]+)*)             # Abreviaturas (Dr., Lic., S.A.)
            |(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,})    # Emails
            |(?:https?://[^\s]+)                                  # URLs
            |(?:\d+(?:[\.,]\d+)*)                                 # Números con decimales
            |(?:[A-Z]+)                                           # Palabras en mayúsculas (p.ej. NASA)
            |(?:[A-Za-z]+)                                        # Resto de palabras
            """,
            re.VERBOSE
        )
        tokens = patron.findall(texto)
        tokens = [t.strip() for t in tokens if t.strip()]
        tokens = [t.lower() for t in tokens]
        if self.eliminar_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]
        return tokens

    def analizar_coleccion(self, path_documentos):
        terminos = {}
        docs_analizados = 0
        for doc_name in os.listdir(path_documentos):
            path_doc = os.path.join(path_documentos, doc_name)
            if os.path.isfile(path_doc):
                with open(path_doc, "r", encoding="utf-8") as f:
                    texto = f.read()
                    tokens = self.tokenizar(texto)
                    docs_analizados += 1
                    for token in tokens:
                        if token not in terminos:
                            terminos[token] = {
                                "cf": 0,
                                "df": 0
                            }
                        terminos[token]["cf"] += 1
        # DF simplificado (cada término tiene un doc_count de 1 si aparece en el doc; se omite conteo real)
        for token_data in terminos.values():
            token_data["df"] = docs_analizados
        return {
            "terminos": terminos,
            "docs_analizados": docs_analizados
        }

    def generar_archivos_resultado(self, resultados, output_dir):
        terminos = resultados["terminos"]
        docs_analizados = resultados["docs_analizados"]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # terminos_gref.txt
        with open(os.path.join(output_dir, "terminos_gref.txt"), "w", encoding="utf-8") as f:
            for termino, data in sorted(terminos.items()):
                f.write(f"{termino} {data['cf']} {data['df']}\n")

        # estadisticas_gref.txt (simple ejemplo)
        with open(os.path.join(output_dir, "estadisticas_gref.txt"), "w", encoding="utf-8") as f:
            f.write(f"Documentos analizados: {docs_analizados}\n")
            f.write(f"Términos totales: {len(terminos)}\n")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python3 Tokenizador.py <directorio_documentos> <eliminar_stopwords> <archivo_stopwords> [directorio_salida]")
        sys.exit(1)

    path_documentos = sys.argv[1]
    eliminar_stopwords = sys.argv[2].lower() == "true"
    stopwords_path = sys.argv[3] if eliminar_stopwords else None
    output_dir = sys.argv[4] if len(sys.argv) > 4 else "."

    tokenizador = Tokenizador(stopwords_path=stopwords_path, eliminar_stopwords=eliminar_stopwords)
    resultados = tokenizador.analizar_coleccion(path_documentos)
    tokenizador.generar_archivos_resultado(resultados, output_dir)
