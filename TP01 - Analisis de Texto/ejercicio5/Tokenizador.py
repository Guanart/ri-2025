#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import json
import sys
import nltk.stem


class Tokenizador:
    def __init__(
        self, stopwords_path=None, eliminar_stopwords=False, stemming=True, stemmer_type="snowball", min_len=1, max_len=20
    ):
        self.stopwords = set()
        self.eliminar_stopwords = eliminar_stopwords
        self.min_len = min_len
        self.max_len = max_len
        self.stemming = stemming
        self.stemmer_type = stemmer_type

        if stopwords_path:
            with open(stopwords_path, "r") as f:
                for line in f:
                    self.stopwords.add(line.strip().lower())

    def tokenizar(self, texto):
        texto = re.sub(r"[^\w\s]|_", "", texto)
        tokens = texto.split()
        tokens = [
            token for token in tokens if token
        ]  # Eliminar tokens vacios (cadenas vacias)
        tokens = [
            token.lower()
            for token in tokens
            if self.min_len <= len(token) <= self.max_len
        ]

        if self.eliminar_stopwords:
            tokens = [token for token in tokens if token not in self.stopwords]

        if self.stemming:
            if self.stemmer_type == "porter":
                stemmer = nltk.stem.PorterStemmer()
            elif self.stemmer_type == "lancaster":
                stemmer = nltk.stem.LancasterStemmer()
            else:
                stemmer = nltk.stem.SnowballStemmer("spanish")
            tokens = [stemmer.stem(token) for token in tokens]
            
        return tokens

    def analizar_coleccion(self, path_documentos) -> dict:
        docs_analizados = 0
        cantidad_tokens = 0
        terminos = (
            {}
        )  # Almacena los terminos como keys, y como values los docid, freqs y DF
        tokens_terms_por_documento = (
            {}
        )  # Almacena los nombres de documentos como key y la cantidad de tokens y terminos como value

        for doc_name in os.listdir(path_documentos):
            path_doc = os.path.join(path_documentos, doc_name)
            with open(path_doc, "r", encoding="utf-8") as f:
                texto = (
                    f.read()
                )  # Podemos leer los archivos completos, ya que no son muy grandes y solo tienen una linea
                tokens = self.tokenizar(texto)
                cantidad_tokens += len(tokens)

                # Ordenar tokens para aplicar corte de control
                tokens.sort()
                i = 0
                tokens_terms_por_documento[doc_name] = {"tokens": 0, "terminos": 0}
                while i < len(tokens):
                    current = tokens[i]
                    count = 1
                    j = i + 1
                    while j < len(tokens) and tokens[j] == current:
                        count += 1
                        j += 1
                    if current not in terminos:
                        terminos[current] = {"docid": [], "freq": [], "cf": 0, "df": 0}
                    # terminos[current]["docid"].append(doc_id)
                    # terminos[current]["freq"].append(count)
                    terminos[current]["cf"] += count
                    terminos[current]["df"] += 1

                    tokens_terms_por_documento[doc_name]["tokens"] += count
                    tokens_terms_por_documento[doc_name]["terminos"] += 1

                    i = j

                docs_analizados += 1

        # Calcular estadisticas y frecuencias
        estadisticas = self.calcular_estadisticas(
            terminos, tokens_terms_por_documento, docs_analizados, cantidad_tokens
        )
        top_10, last_10 = self.calcular_frecuencias(terminos)

        return {
            "terminos": terminos,
            "estadisticas": estadisticas,
            "frecuencias": {"top_10": top_10, "last_10": last_10},
        }

    def analizar_coleccion_trec(self, path_coleccion) -> dict:
        """
        Procesa la colección TREC (un único archivo con <DOC> ... </DOC> en cada documento).
        """
        docs_analizados = 0
        cantidad_tokens = 0
        terminos = {}  # Almacena los términos y sus frecuencias globales
        tokens_terms_por_documento = {}  # Almacena, para cada documento (usamos el DOCNO o generamos un id), la cantidad de tokens y términos

        with open(path_coleccion, "r", encoding="utf-8") as f:
            contenido = f.read()
        # Extraer documentos delimitados por <DOC> ... </DOC>
        docs = re.findall(r"<DOC>(.*?)</DOC>", contenido, flags=re.DOTALL)

        for idx, doc in enumerate(docs):
            # Extraer el número de documento si está presente
            docno_match = re.search(r"<DOCNO>(.*?)</DOCNO>", doc)
            doc_id = docno_match.group(1).strip() if docno_match else f"doc_{idx+1}"
            # Eliminar todas las etiquetas XML
            texto = re.sub(r"<[^>]+>", " ", doc)
            tokens = self.tokenizar(texto)
            cantidad_tokens += len(tokens)

            tokens.sort()
            tokens_terms_por_documento[doc_id] = {"tokens": 0, "terminos": 0}
            i = 0
            while i < len(tokens):
                current = tokens[i]
                count = 1
                j = i + 1
                while j < len(tokens) and tokens[j] == current:
                    count += 1
                    j += 1
                if current not in terminos:
                    terminos[current] = {"docid": [], "freq": [], "cf": 0, "df": 0}
                terminos[current]["cf"] += count
                terminos[current]["df"] += 1

                tokens_terms_por_documento[doc_id]["tokens"] += count
                tokens_terms_por_documento[doc_id]["terminos"] += 1

                i = j

            docs_analizados += 1

        estadisticas = self.calcular_estadisticas(terminos, tokens_terms_por_documento, docs_analizados, cantidad_tokens)
        top_10, last_10 = self.calcular_frecuencias(terminos)
        return {
            "terminos": terminos,
            "estadisticas": estadisticas,
            "frecuencias": {"top_10": top_10, "last_10": last_10},
        }

    def calcular_frecuencias(self, terminos):
        # Top 10 términos más y menos frecuentes
        items = list(terminos.items())
        items_sorted = sorted(items, key=lambda x: x[1]["cf"])
        last_10 = items_sorted[:10]
        top_10 = items_sorted[-10:][::-1]
        return top_10, last_10

    def calcular_estadisticas(
        self, terminos, tokens_terms_por_documento, docs_analizados, cantidad_tokens
    ):
        num_terminos = len(terminos)  # complejidad O(1)
        promedio_tokens = cantidad_tokens / docs_analizados
        promedio_terminos = num_terminos / docs_analizados

        cant_terminos = 0
        sum_largo_terminos = 0
        terminos_una_vez = []
        for term, freq in terminos.items():  # complejidad O(n)
            cant_terminos += 1
            sum_largo_terminos += len(term)
            if freq["cf"] == 1:
                terminos_una_vez.append(term)
        largo_promedio_termino = sum_largo_terminos / cant_terminos

        doc_corto = next(iter(tokens_terms_por_documento.values()))
        doc_largo = next(iter(tokens_terms_por_documento.values()))
        for doc_name, data in tokens_terms_por_documento.items():
            if data["tokens"] < doc_corto["tokens"]:
                doc_corto = data
            if data["tokens"] > doc_largo["tokens"]:
                doc_largo = data
        doc_corto = {"tokens": doc_corto["tokens"], "terminos": doc_corto["terminos"]}
        doc_largo = {"tokens": doc_largo["tokens"], "terminos": doc_largo["terminos"]}

        return {
            "docs_analizados": docs_analizados,
            "cantidad_tokens": cantidad_tokens,
            "num_terminos": num_terminos,
            "promedio_tokens": promedio_tokens,
            "promedio_terminos": promedio_terminos,
            "largo_promedio_termino": largo_promedio_termino,
            "doc_corto": doc_corto,
            "doc_largo": doc_largo,
            "terminos_una_vez": len(terminos_una_vez),
        }

    def generar_archivos_salida(self, resultados, output_dir):
        terminos = resultados["terminos"]
        estadisticas = resultados["estadisticas"]
        frecuencias = resultados["frecuencias"]

        # Archivo terminos.txt
        with open(os.path.join(output_dir, "terminos.txt"), "w") as f:
            for termino, data in sorted(terminos.items()):
                f.write(f"{termino} {data['cf']} {data['df']}\n")

        # Archivo estadisticas.txt
        with open(os.path.join(output_dir, "estadisticas.txt"), "w") as f:
            f.write(f"Documentos analizados: {estadisticas['docs_analizados']}\n")
            f.write(f"Cantidad de Tokens: {estadisticas['cantidad_tokens']}\n")
            f.write(f"Cantidad de Términos: {estadisticas['num_terminos']}\n")
            f.write(f"Promedio Tokens: {estadisticas['promedio_tokens']}\n")
            f.write(f"Promedio Términos: {estadisticas['promedio_terminos']}\n")
            f.write(
                f"Largo promedio de los Términos: {estadisticas['largo_promedio_termino']}\n"
            )
            f.write(
                f"Cantidad de tokens del documento más corto y más largo: {estadisticas['doc_corto']['tokens']} {estadisticas['doc_largo']['tokens']}\n"
            )
            f.write(
                f"Cantidad de términos del documento más corto y más largo: {estadisticas['doc_corto']['terminos']} {estadisticas['doc_largo']['terminos']}\n"
            )
            f.write(
                f"Términos con frecuencia 1 en la colección: {estadisticas['terminos_una_vez']}\n"
            )

        # Archivo frecuencias.txt
        with open(os.path.join(output_dir, "frecuencias.txt"), "w") as f:
            f.write("10 términos más frecuentes:\n")
            for termino, data in frecuencias["top_10"]:
                f.write(f"{termino} {data['cf']}\n")
            f.write("\n10 términos menos frecuentes:\n")
            for termino, data in frecuencias["last_10"]:
                f.write(f"{termino} {data['cf']}\n")


if __name__ == "__main__":
    import time

    path_documentos = "datos/vaswani/corpus/doc-text.trec"

    # Ejecutar con PorterStemmer
    stemmer = "porter"
    tokenizador = Tokenizador(stopwords_path=None, eliminar_stopwords=False, stemming=True, stemmer_type=stemmer)
    start_time = time.time()
    resultados_porter = tokenizador.analizar_coleccion_trec(path_documentos)
    porter_time = time.time() - start_time
    if not os.path.exists(f"output_{stemmer}"):
        os.makedirs(f"output_{stemmer}")
    tokenizador.generar_archivos_salida(resultados_porter, f"output_{stemmer}")

    # Ejecutar con LancasterStemmer
    stemmer = "lancaster"
    tokenizador = Tokenizador(stopwords_path=None, eliminar_stopwords=False, stemming=True, stemmer_type="lancaster")
    start_time = time.time()
    resultados_lancaster = tokenizador.analizar_coleccion_trec(path_documentos)
    lancaster_time = time.time() - start_time
    if not os.path.exists(f"output_{stemmer}"):
        os.makedirs(f"output_{stemmer}")
    tokenizador.generar_archivos_salida(resultados_lancaster, f"output_{stemmer}")

    # Comparación de resultados
    print("Resultados PorterStemmer:")
    print(f"Tokens únicos: {len(resultados_porter['terminos'])}")
    print(f"Tiempo de ejecución: {porter_time:.2f} segundos")

    print("\nResultados LancasterStemmer:")
    print(f"Tokens únicos: {len(resultados_lancaster['terminos'])}")
    print(f"Tiempo de ejecución: {lancaster_time:.2f} segundos")