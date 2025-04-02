#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
from langdetect import detect
import numpy as np


class TokenizadorLenguaje:
    def __init__(self, min_len=1, max_len=20):
        self.min_len = min_len
        self.max_len = max_len

    def tokenizar(self, texto, w=None):
        # Se conserva la mayoría de caracteres especiales (incluyendo acentos) para identificación de lenguajes,
        # pero se eliminan otros que no son relevantes.
        texto = re.sub(
            r"[^\w\s¿?¡!'áéíóúüñçàèìòùâêîôûäëïöü]", "", texto, flags=re.UNICODE
        )
        if w:
            # Genera n-gramas de longitud w a partir del texto (caracteres consecutivos)
            tokens = []
            for i in range(len(texto) - w + 1):
                tokens.append(texto[i : i + w])
        else:
            tokens = texto.split()
        tokens = [token for token in tokens if token]  # Eliminar tokens vacíos
        tokens = [
            token.lower()
            for token in tokens
            if self.min_len <= len(token) <= self.max_len
        ]
        return tokens

    def entrenar_modelos(self, path_training):
        """
        Entrena un modelo de frecuencia de letras (unigrama) y de combinaciones (bigramas)
        para cada idioma en el conjunto de entrenamiento.
        """
        modelos_frecuencia = {}
        modelos_combinaciones = {}
        for idioma, filepath in path_training.items():
            modelos_frecuencia[idioma] = {}
            modelos_combinaciones[idioma] = {}
            with open(filepath, "r", encoding="iso-8859-1") as f:
                for line in f:
                    # Modelo de frecuencia de letras (unigrama)
                    tokens_frecuencia = self.tokenizar(line, w=1)
                    for token in tokens_frecuencia:
                        modelos_frecuencia[idioma][token] = (
                            modelos_frecuencia[idioma].get(token, 0) + 1
                        )
                    # Modelo de combinaciones (bigramas)
                    tokens_combinaciones = self.tokenizar(line, w=2)
                    for token in tokens_combinaciones:
                        modelos_combinaciones[idioma][token] = (
                            modelos_combinaciones[idioma].get(token, 0) + 1
                        )
        return modelos_frecuencia, modelos_combinaciones

    def identificar_lenguaje(
        self, path_test, modelos_frecuencia, modelos_combinaciones
    ):
        """
        Identifica el idioma de cada línea del archivo de prueba utilizando:
          - La distribución de la frecuencia de letras (unigrama).
          - La distribución de combinaciones de letras (bigramas).
        Se comparan las distribuciones normalizadas del texto con las de los modelos entrenados también normalizadas, usando la distancia (suma de diferencias absolutas). El más cercano a 0 es el idioma más probable.
        También se utiliza langdetect para la comparación.
        Devuelve una lista de diccionarios con las predicciones y el ID del texto.
        """

        # Función auxiliar: normalizar las frecuencias a distribuciones relativas (divide la frecuencia absoluta de un token por el total de tokens en el texto)
        # Se usa para evitar que un token con alta frecuencia en un idioma influya demasiado en la distancia
        def normalizar(dic):
            total = sum(dic.values())
            return {k: v / total for k, v in dic.items()} if total > 0 else dic

        # Función auxiliar: distancia entre dos distribuciones
        def distancia(dic1, dic2):
            keys = set(dic1.keys()) | set(dic2.keys())
            total_distance = 0
            for k in keys:
                diff = abs(dic1.get(k, 0) - dic2.get(k, 0))
                total_distance += diff
            return total_distance

        # Normalizar los modelos entrenados para cada idioma
        norm_modelos_frecuencia = {
            idioma: normalizar(modelo) for idioma, modelo in modelos_frecuencia.items()
        }
        norm_modelos_combinaciones = {
            idioma: normalizar(modelo)
            for idioma, modelo in modelos_combinaciones.items()
        }

        resultados = []
        with open(path_test, "r", encoding="iso-8859-1") as f:
            for i, line in enumerate(f):
                texto = line.strip()
                # Calcular la distribución de frecuencia (unigrama) para el texto de prueba
                freq_line = {}
                for token in self.tokenizar(texto, w=1):
                    freq_line[token] = freq_line.get(token, 0) + 1
                norm_freq_line = normalizar(freq_line)

                # Calcular la distribución de combinaciones (bigramas) para el texto de prueba
                comb_line = {}
                for token in self.tokenizar(texto, w=2):
                    comb_line[token] = comb_line.get(token, 0) + 1
                norm_comb_line = normalizar(comb_line)

                # Comparar la distribución del texto con la de cada idioma en los modelos (método frecuencia)
                dist_frecuencia = {}
                for idioma, modelo in norm_modelos_frecuencia.items():
                    dist_frecuencia[idioma] = distancia(modelo, norm_freq_line)
                pred_frecuencia = min(
                    dist_frecuencia, key=dist_frecuencia.get
                )  # Con key=dist_frecuencia.get en lugar de comparar directamente las claves del diccionario, se comparan los valores asociados a esas claves

                # Comparar la distribución del texto con la de cada idioma en los modelos (método combinaciones)
                dist_combinaciones = {}
                for idioma, modelo in norm_modelos_combinaciones.items():
                    dist_combinaciones[idioma] = distancia(modelo, norm_comb_line)
                pred_combinaciones = min(dist_combinaciones, key=dist_combinaciones.get)

                # Langdetect
                pred_langdetect = detect(texto)

                resultados.append(
                    {
                        "texto": i,
                        "frecuencia": pred_frecuencia,
                        "combinaciones": pred_combinaciones,
                        "langdetect": pred_langdetect,
                    }
                )

        return resultados

    def generar_archivo_salida(self, resultados, solucion):
        correctos_frecuencia = 0
        correctos_combinaciones = 0
        correctos_langdetect = 0
        with open("resultados.txt", "w", encoding="iso-8859-1") as f:
            for i, resultado in enumerate(resultados):
                print(f"Texto: {resultado['texto']}")
                print(f"Predicción Frecuencia: {resultado['frecuencia']}")
                print(f"Predicción Combinaciones: {resultado['combinaciones']}")
                print(f"Predicción LangDetect: {resultado['langdetect']}")
                print(f"Solución: {solucion[i]}")
                print()

                if resultado["frecuencia"] == solucion[i]:
                    correctos_frecuencia += 1
                if resultado["combinaciones"] == solucion[i]:
                    correctos_combinaciones += 1
                if resultado["langdetect"] == solucion[i][:2].lower():
                    correctos_langdetect += 1

            print("Resultados finales:")
            print(
                f"Método Frecuencia: {correctos_frecuencia}/{len(solucion)} correctos"
            )
            print(
                f"Método Combinaciones: {correctos_combinaciones}/{len(solucion)} correctos"
            )
            print(
                f"Método LangDetect: {correctos_langdetect}/{len(solucion)} correctos"
            )
            f.write("Resultados finales:\n")
            f.write(
                f"Método Frecuencia: {correctos_frecuencia}/{len(solucion)} correctos\n"
            )
            f.write(
                f"Método Combinaciones: {correctos_combinaciones}/{len(solucion)} correctos\n"
            )
            f.write(
                f"Método LangDetect: {correctos_langdetect}/{len(solucion)} correctos\n"
            )


if __name__ == "__main__":
    # Archivos de entrenamiento y prueba
    path_training = {
        "English": "datos/languageIdentificationData/training/English",
        "French": "datos/languageIdentificationData/training/French",
        "Italian": "datos/languageIdentificationData/training/Italian",
    }
    path_test = "datos/languageIdentificationData/test"
    path_solution = "datos/languageIdentificationData/solution"  # Para comparación (si es necesario)

    tokenizador = TokenizadorLenguaje()

    # Entrenar modelos de frecuencia (unigrama) y de combinaciones (bigramas)
    modelos_frecuencia, modelos_combinaciones = tokenizador.entrenar_modelos(
        path_training
    )

    # Identificar lenguajes en el conjunto de prueba
    resultados = tokenizador.identificar_lenguaje(
        path_test, modelos_frecuencia, modelos_combinaciones
    )

    # Comparar con la solución provista (si existe) y con langdetect
    with open(path_solution, "r", encoding="iso-8859-1") as f:
        solucion = [line.strip().split()[1] for line in f.readlines()]

    # Generar archivo de salida con los resultados
    tokenizador.generar_archivo_salida(resultados, solucion)
