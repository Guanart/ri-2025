**Estructuras de Datos**

**Fecha entrega: 28/05/2025**

Para la entrega del TP resuelto arme un único archivo comprimido (.tar.gz) y envielo a través del siguiente formulario: [https://forms.gle/2R4K8wkKZXnVnHJW8](https://forms.gle/2R4K8wkKZXnVnHJW8)  el cual se encontrará habilitado hasta la fecha de entrega establecida.  
Bibliografía sugerida: MIR \[1\] Capítulos 8, Croft \[2\] Capítulo 5, MAN \[3\] Capítulos 4\.

1) Codifique un script que indexe una colección[^1] que requiera el volcado parcial a disco (asumiendo que existe un límite de memoria) implementando el método  *BSBI* visto en clase*.* Para esto su script debe recibir un parámetro *n* que indica cada cuántos documentos se debe hacer el volcado a disco. Al finalizar, debe unir (merge) los índices parciales. Para las pruebas use la colección snapshot de Wikipedia[^2] y varios valores de *n* (por ejemplo, n \= 10% del tamaño de la colección). Registre los tiempos de indexación y de merge por separado. Grafique la distribución de tamaños de las posting lists. Calcule el overhead de su índice respecto de la colección. ¿Qué conclusiones se pueden extraer?  
     
   1.1) Agregue un *script* que cargue el vocabulario de la colección en memoria, permita recuperar una posting completa de un término y la muestre por pantalla. Para cada documento retornado se deberá mostrar el nombre, el  docID asignado  durante la creación del índice y la frecuencia en el siguiente formato:   
     
* DocName:docID:Frecuencia  
    
  Utilice la colección de *debug* para calibrar su script y verificar que la salida sea correcta.   
    
2) Codifique un *script* que implemente la estrategia TAAT vista en clase y sobre el índice creado en el ejercicio 1 permita realizar operaciones sobre conjuntos para buscar por dos o tres términos utilizando los operadores AND, OR y NOT.   
   Su script debe permitir el procesamiento de consultas del tipo:  
     
* *((t1 AND t2) OR t3)*   
* *((t1 AND NOT t2) OR NOT T3))*

  Como salida su script debe retornar el nombre y el docID de los documentos que satisfacen la consulta[^3].

3) Utilizando el código e índice anteriores ejecute corridas  con el siguiente subset de queries[^4] (filtre solo los de 2 y 3 términos que estén en el vocabulario de su colección) y mida el tiempo de ejecución en cada caso. Para ello, utilice los siguientes patrones booleanos:  
     
   1) Queries |q| \= 2  
* t1 AND t2  
* t1 OR t2  
* t1 NOT t2


  2) Queries |q| \= 3  
* t1 AND t2 AND t3  
* (t1 OR t2) NOT t3  
* (t1 AND t2) OR t3

  ¿Puede relacionar los tiempos de ejecución con los tamaños de las listas? (pruebe con el índice en disco o cargándolo completamente en memoria antes). ¿Qué conclusiones se pueden extraer?

4) Codifique un script que implemente la estrategia DAAT vista en clase y sobre el índice creado en el ejercicio 1 permita resolver consultas usando el modelo vectorial utilizando la métrica del coseno como medida de similitud. Dada una consulta su script debe retornar los top-k documentos de score mayor.   
     
   Su script debe mostrar como salida el nombre, el  docID y  el  score (ordenado  por score) con el  siguiente formato   
     
* DocName:docID:Score


5) Agregue *skip lists* a su índice del ejercicio 1 y ejecute un conjunto de consultas AND sobre el índice original y luego usando los punteros. Compare los tiempos de ejecución con los del ejercicio 3\.   
   5.1) Agregue un script que permita recuperar las skips list para un término dado. En este caso la salida deberá ser una lista de docName:docID ordenada por docName.  
     
   Utilice la colección para debugging para calibrar su script. 

6) Sobre la colección Dump10k[^5] escriba un programa que realice una evaluación TAAT y otro usando DAAT. Compare los tiempos de ejecución para un conjunto de queries dados[^6]. Separe su análisis por longitud de queries y de posting lists.  
     
7) Comprima el índice del ejercicio 1 utilizando Variable-Length Codes (VByte) para los docIDs y Elias-gamma para las frecuencias (almacene docIDs y frecuencias en archivos separados). Calcule tiempos de compresión/descompresión del índice completo y tamaño resultante en cada caso. Realice dos experimentos, con y sin DGaps. Compare los tamaños de los índices resultantes.  
     
   7.1) Agregue un script que permita recuperar de disco la posting list de un término  dado y la versión comprimida de dicha lista. 

   

**Bibliografía**

\[1\] Ricardo Baeza-Yates and Berthier Ribeiro-Neto. Modern Information Retrieval: The Concepts and Technology Behind Search. Addison-Wesley Publishing Company, USA, 2nd edition, 2008\.

\[2\] Bruce Croft, Donald Metzler, and Trevor Strohman. Search Engines: Information Retrieval in Practice. Addison-Wesley Publishing Company, USA, 1st edition, 2009\.

\[3\] Christopher D. Manning, Prabhakar Raghavan, and Hinrich Sch ̈utze. Introduction to Information Retrieval. Cambridge University Press, New York, NY, USA, 2008\.

\[4\] Stefan Buttcher. and Charles L. A. Clarke and Gordon V. Cormack. Information Retrieval: Implementing and Evaluating Search Engines. MIT Press,  2010\.

[^1]:  Almacene docID o docID+frecuencia de acuerdo a un parámetro de entrada.

[^2]:  http://dg3rtljvitrle.cloudfront.net/wiki-small.tar.gz(debug), http://dg3rtljvitrle.cloudfront.net/wiki-large.tar.gz

[^3]:  [https://github.com/bastikr/boolean.py](https://github.com/bastikr/boolean.py) 

[^4]:  [https://github.com/tolosoft-academia/RI\_2025/blob/main/data/EFF-10K-queries.txt](https://github.com/tolosoft-academia/RI_2025/blob/main/data/EFF-10K-queries.txt) 

[^5]:  [http://www.tyr.unlu.edu.ar/tallerIR/2014/data/dump10k.tar.gz](http://www.tyr.unlu.edu.ar/tallerIR/2014/data/dump10k.tar.gz) 

[^6]:  [http://www.labredes.unlu.edu.ar/sites/www.labredes.unlu.edu.ar/files/site/data/ri/queriesDump10K.txt.tar.gz](http://www.labredes.unlu.edu.ar/sites/www.labredes.unlu.edu.ar/files/site/data/ri/queriesDump10K.txt.tar.gz) 