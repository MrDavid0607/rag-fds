# Análisis de resultados (Fase 7)

**Estado: observaciones del asistente basadas en los datos guardados (`eval/respuestas_*.json`, `eval/resultados_*.json`, `eval/diag_*.json`).**
Las conclusiones de **exactitud de las respuestas y de correspondencia de las citas con el PDF las confirma el autor** (ver `eval/revision_manual.md`
y `eval/revision_manual/index.html`). Hasta entonces, léase como hipótesis bien documentadas, no como veredictos.

> **Alcance.** Son 10 preguntas respondibles y 2 sin respuesta, una sola corrida por configuración y un evaluador local de 8 B. El conjunto permite una comparación
> **didáctica** entre top-k 3 y top-k 6; **no demuestra** que una configuración sea mejor en general.

## 1. Comparación top-k 3 vs top-k 6

| | top-k 3 | top-k 6 |
|---|---|---|
| Faithfulness (promedio, 10 casos) | 0.892 | 0.867 |
| Context Precision (promedio) | 1.000 | 1.000 |
| Context Recall (promedio) | 0.910 (10 casos) | 1.000 (**9 casos**: e09 falló) |
| Respuestas del tipo "No hay evidencia" en respondibles | 2 (e09, e10) | 0 |
| Tiempo de generación medio / tokens de prompt | 20.6 s / 1 208 | 24.3 s / 1 995 |
| Tiempo de evaluación RAGAS | 19.4 min | 36.2 min |

Qué dicen (y qué no) los números:
- **Context Precision = 1.00 en los 20 casos**: la métrica no discrimina aquí (techo). El filtro por producto deja casi todo el contexto en el documento correcto.
- **Context Recall** sube con top-k 6 en e07 (0.60 → 1.00) y e10 (0.50 → 1.00): con 3 fragmentos, las preguntas que necesitan **dos secciones o dos documentos** se quedan sin parte de la evidencia.
- **Faithfulness** baja un poco con top-k 6, pero la causa está en el **evaluador y en las citas**, no en inventos del generador (ver §3.D). Diferencias de 0.02-0.03 con 10 preguntas son ruido.
- Las dos configuraciones fallan igual en **e12** (producto inexistente): más fragmentos no arreglan ese error.

## 2. Respuestas a las dos preguntas sin respuesta

| Pregunta | top-k 3 | top-k 6 |
|---|---|---|
| e11 (rendimiento del Acrolatex; la FDS no lo trae) | Reconoce la falta de evidencia | Reconoce la falta de evidencia |
| e12 (Intergard 475HS; no está en el corpus) | **Inventa**: "Según la ficha del Intergard 475HS [1]…" con primeros auxilios de otro producto | **Inventa** (sin nombrar el producto, cita [1]) |

(Pendiente de confirmación del autor en `revision_manual.md`.)

## 3. Errores observados, por causa

### A. Recuperación
- **e10, top-k 3** — recupera 3 fragmentos de las secciones 7, 7 y 9 y **ninguno de la sección 4**; el generador contesta "No hay evidencia suficiente… contacto con la piel" y solo responde el almacenamiento. Con top-k 6 aparece el fragmento de la sección 4 y la respuesta es completa. El rechazo es coherente con lo recuperado: el fallo es de recuperación.
- **e08, top-k 3** — falta el fragmento de la sección 5; el generador completa "extintor de polvo ABC" con la frase P370+P378 de la sección 2 y omite espuma, CO₂ y "no usar agua a chorro" (Faithfulness 0.67).
- **e07, top-k 3** — falta el fragmento de la densidad de la ficha de 2019; la respuesta afirma que "no se menciona esta información en la versión 2019", pero la ficha de 2019 sí la trae (1371,4 kg/m³; ver PDF, pág. 5). Con top-k 6 está el fragmento y la respuesta es correcta.
- **e09 (ambas configuraciones)** — (i) el filtro de producto devuelve **6 productos** (4 esmaltes Top Quality y 2 Pintulaca) porque el nombre comparte palabras raras y, en comparaciones, se desactiva el estrechamiento por código numérico (1772); (ii) la sección 2, donde están la clasificación H360 y las categorías de líquido inflamable (H225/H226), **no se recupera**: los fragmentos son de la sección 11 (toxicología). Resultado: la respuesta con top-k 6 acierta la toxicidad para la reproducción del Pintulaca Rojo Claro, pero **omite la categoría de líquido inflamable**, parte de la pregunta; con top-k 3 el generador dice "no hay evidencia" aunque dos líneas después afirma que "ambos" no cumplen criterios (contradictorio).
- **e12** — sin producto coincidente no hay filtro por nombre; la búsqueda trae primeros auxilios (sección 4) de otros productos de International.

### B. Extracción y metadatos
- **Metadatos de producto erróneos en 8 fichas de AkzoNobel/International** (FDS 82, 83, 84, 85, 95, 96, 98, 99): `producto` quedó como «X International.» / «International. X» (el logo leído por el OCR). Se nota en la lista de fuentes de e12 ("AkzoNobel · X International. · …") y deja esas fichas sin filtro por producto; además contamina el encabezado de sus fragmentos. **No se corrigió** para no invalidar la evaluación ya corrida; es un defecto real de `metadatos.py` (la corrección del caso FDS 80 no cubrió estas fichas).
- **Etiqueta y valor separados** (formularios, p. ej. FDS 62, 87): ya documentado en la Fase 3; las preguntas e02 y e10 se sustituyeron por otras con datos literales para que la evaluación mida el RAG y no la extracción. Esas fichas siguen siendo un caso difícil que **no** quedó cubierto por la evaluación.

### C. Generación
- **Citas que apuntan a otro producto (e09, top-k 6)**: la afirmación "el Top Quality Negro 1772 no está clasificado" cita [1][2][3][4][6]; [1] es de esa ficha, pero [2], [3], [4] y [6] son de los esmaltes Top Quality gris plata, rojo bermellón y azul medio, y de la Pintulaca Blanco. La afirmación coincide con la ficha 35, pero **las citas no son todas correctas** (el autor lo confirma contra el PDF).
- **e12**: el modelo atribuye al "Intergard 475HS" texto de otra ficha y no usa la frase de falta de evidencia; el aviso determinista de "variante sin ficha" no se activa porque ningún producto coincide.
- **Ambigüedad de redacción (e04)**: "su número CAS" no aclara que el CAS 13463-67-7 es el del dióxido de titanio, no del producto.

### D. El evaluador (RAGAS con `llama3.1:8b`)
- **Falso negativo (e07, top-k 6; Faithfulness 0.50)**: el evaluador declara no respaldada la afirmación "36 meses en 2019 → 12 meses en 2021", pero los contextos [1] y [2] contienen "12 meses" y "36 meses". El 0.50 no refleja un error de la respuesta.
- **Literalidad (e04, ambas configuraciones; Faithfulness 0.50)**: marca "el número CAS del Sigmadur es 13463-67-7" como no respaldado porque el contexto lo asigna al dióxido de titanio. Es defendible por la ambigüedad de la redacción, pero es el único punto que baja la puntuación de una respuesta que cumple la referencia.
- **No determinismo**: al repetir el diagnóstico de e09 (top-k 6) con la misma respuesta y los mismos contextos, el evaluador dio 3 de 3 afirmaciones respaldadas (Faithfulness 1.00) frente a 0.67 en la corrida oficial. Con temperatura 0 y semilla fija, la repetición no es idéntica; las puntuaciones individuales tienen ruido.
- **Fallo de formato (e09, top-k 6, Context Recall)**: `RagasOutputParserException` dos veces (JSON no interpretable tras los reintentos); queda como `NaN`.
- **Artefacto de las citas**: las marcas `[n]` bajaban la Faithfulness (hallazgo del piloto); se quitan solo para puntuar.
- **Cobertura**: Faithfulness no mide completitud (e09 top-k 6 omite la categoría de inflamabilidad y aun así no lo refleja); Context Precision es siempre 1.00.

## 4. Configuración elegida y por qué

**Se elige top-k 6** (con la advertencia de que es una elección sobre 10 preguntas):
1. Fue la única que recuperó la evidencia de **ambas secciones o ambos documentos** en e07, e08 y e10, y por eso contestó donde top-k 3 se quedó corto o rechazó.
2. Context Recall 1.00 (9 casos válidos) frente a 0.91.
3. Los puntos donde saca menos Faithfulness (e07, e09) se explican por el evaluador y por citas a fichas de otros productos, no por datos inventados en los casos respondibles.
4. Costo moderado: +3.7 s por respuesta (+18 %) y prompts de ~2 000 tokens, que caben sin problema en `num_ctx` 8 192.

Contra top-k 6: más contexto aumenta la oportunidad de **citas a fichas ajenas** (e09) y el doble de tiempo de evaluación; y no resuelve e12.

## 5. Mejoras identificadas (NO aplicadas)

Cualquier cambio exige repetir la evaluación completa (~90 min) y declararlo como una nueva versión, para no ajustar el sistema a las 12 preguntas:
1. Corregir los metadatos de producto de las 8 fichas AkzoNobel (y reconstruir el índice).
2. En comparaciones, mantener el estrechamiento por código numérico dentro de cada producto.
3. Dar prioridad a la sección 2 cuando la pregunta habla de "clasificación" o de categorías de peligro (hoy el bonus sugiere la sección 11).
4. Activar el aviso de "producto sin ficha" también cuando el nombre propio de la pregunta no coincide con ninguna ficha (caso e12).
5. Evaluador: probar otro modelo o repetir cada puntuación varias veces y promediar.
