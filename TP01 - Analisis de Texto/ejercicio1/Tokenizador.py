#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import json

'''
El Tokenizador debe retornar:
- Lista de términos y su DF
- Cantidad de tokens
- Cantidad de términos 
- Cantidad de documentos procesados  
'''
class Tokenizador:
    def __init__(self):
        pass

    def tokenizar(self, texto):
        # Eliminar caracteres especiales (deja caracteres alfanumericos y espacios)
        texto = re.sub(r'[^\w\s]|_', '', texto)   # \w incluye los guiones bajos "_"?  SI
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
        terminos = {}   # Almacena los terminos como keys, y como values los docid, freqs y DF
        
        for doc_id, doc_name in enumerate(os.listdir(path_documentos), start=0):
            path_doc = os.path.join(path_documentos, doc_name)
            with open(path_doc, 'r') as f:
                texto = f.read()  # Podemos leer los archivos completos, ya que no son muy grandes y solo tienen una linea
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
                    i = j

                docs_analizados += 1

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
with open('./output_punto1.json', 'w') as f:
    json.dump(resultados, f, indent=2)