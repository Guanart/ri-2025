#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('punkt_tab')

class Tokenizador:
    def __init__(self):
        pass

    def tokenizar(self, texto):
        tokens = word_tokenize(texto)
        return tokens

    def analizar_coleccion(self, path_documentos) -> dict:
        docs_analizados = 0
        cantidad_tokens = 0
        terminos = {}   # Almacena los terminos con su DF. Ejemplo: {"casa": 3, "perro": 5, "gato": 2}

        for doc_name in os.listdir(path_documentos):
            path_doc = os.path.join(path_documentos, doc_name)
            with open(path_doc, 'r') as f:
                texto = f.read()
                tokens = self.tokenizar(texto)
                cantidad_tokens += len(tokens)
                # Calcular DF
                unique_tokens =  set(tokens)      # Limpio repetidos, para poder calcular la DF sumando +1 por token
                for token in tokens:
                    terminos[token] = terminos.get(token, 0) + 1
                docs_analizados += 1

        # {"data": [
        #       {"term": "reloj", "docid": [2, 3, 5,... 9543], "freq": [23, 42, 12,... 20], "df": 97},
        #       {"term": "casa", "docid": [2, 3, 5,... 9543], "freq": [23, 42, 12,... 20], "df": 97},
        #       {"term": "perro", "docid": [2, 3, 5,... 9543], "freq": [23, 42, 12,... 20], "df": 97},
        # ]}
        # Asi esta formato collection_data.json. Por ahora, solo guardo el termino y su df
        return {
            "data": terminos,
            "statistics": {
                "N": docs_analizados,
                "num_terms": len(terminos),         # debe dar 20 para collection_test
                "num_tokens": cantidad_tokens   # debe dar 793254 para collection_test
            }
        }

tokenizador = Tokenizador()
resultados = tokenizador.analizar_coleccion('./datos/collection_test/TestCollection/')
print(resultados)