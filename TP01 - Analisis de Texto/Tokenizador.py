#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re

class Tokenizador:
    def __init__(self):
        pass

    def tokenizar(self, texto):
        # Eliminar caracteres especiales (deja caracteres alfanumericos y espacios)
        texto = re.sub(r'[^\w\s]', '', texto)   # \w incluye los guiones bajos "_"?
        # Split por espacios
        tokens = texto.split()
        # Eliminar tokens vacios (cadenas vacias)
        tokens = [token for token in tokens if token]
        # Pasar a minusculas
        tokens = [token.lower() for token in tokens]
        return tokens

    def analizar_coleccion(self, path_documentos) -> dict:
        docs_analizados = 0
        cantidad_tokens = 0
        terminos = {}   # Almacena los terminos en el formato collection_data.json

        for doc_id, doc_name in enumerate(os.listdir(path_documentos), start=1):    # doc0.txt tendra id=1
            path_doc = os.path.join(path_documentos, doc_name)
            with open(path_doc, 'r') as f:
                texto = f.read()  # Podemos leer los archivos completos, ya que no son muy grandes y solo tienen una linea
                tokens = self.tokenizar(texto)
                cantidad_tokens += len(tokens)

                # Por cada token, 
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