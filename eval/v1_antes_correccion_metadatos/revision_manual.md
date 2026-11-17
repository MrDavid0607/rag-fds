# Revisión manual (Fase 7)

Plantilla preparada por el asistente. **Las casillas y conclusiones de exactitud las llena el autor** mirando los PDF; el asistente solo aporta datos y pre-chequeos automáticos. Versión web con el PDF al lado: `eval/revision_manual/index.html`.

Casos: las 2 preguntas sin respuesta (e11, e12) y 3 respondibles con las puntuaciones más bajas o con fallos (e04, e07, e09). Otros casos con rechazos o respuestas incompletas (e08, e10) se comentan en `eval/analisis_resultados.md`.

## A. Preguntas sin respuesta sustentada en el corpus

### e11 — ¿Cuál es el rendimiento teórico, en m² por galón, del Acrolatex 50 3508 de Pintuco?

**Comportamiento esperado:** Reconocer que no hay evidencia suficiente: la FDS del Acrolatex 50 3508 (producto sí presente en el corpus) no informa rendimiento ni cobertura (eso se encuentra en fichas técnicas, no en FDS). No debe inventar un valor.

**topk3 (top-k 3)** — el sistema SÍ dijo que no hay evidencia

> No hay evidencia suficiente en las FDS disponibles para el rendimiento teórico, en m² por galón, del Acrolatex 50 3508 de Pintuco.

Fragmentos recuperados: [1] fds057-acrolatex-50-3508-pintuco · pág. 1 · sección 1; [2] fds057-acrolatex-50-3508-pintuco · pág. 5 · sección 9; [3] fds057-acrolatex-50-3508-pintuco · pág. 8 · sección 11

- Fuentes que listó el sistema: (ninguna)
- **Revisión del autor** — ¿reconoce la falta de evidencia o inventa?  ☐ reconoce  ☐ inventa  ☐ parcial
- Observaciones: 

**topk6 (top-k 6)** — el sistema SÍ dijo que no hay evidencia

> No hay evidencia suficiente en las FDS disponibles para determinar el rendimiento teórico, en m² por galón, del Acrolatex 50 3508 de Pintuco.

Fragmentos recuperados: [1] fds057-acrolatex-50-3508-pintuco · pág. 1 · sección 1; [2] fds057-acrolatex-50-3508-pintuco · pág. 5 · sección 9; [3] fds057-acrolatex-50-3508-pintuco · pág. 8 · sección 11; [4] fds057-acrolatex-50-3508-pintuco · pág. 5-6 · sección 9; [5] fds057-acrolatex-50-3508-pintuco · pág. 6 · sección 9; [6] fds057-acrolatex-50-3508-pintuco · pág. 4 · sección 8

- Fuentes que listó el sistema: (ninguna)
- **Revisión del autor** — ¿reconoce la falta de evidencia o inventa?  ☐ reconoce  ☐ inventa  ☐ parcial
- Observaciones: 

### e12 — ¿Qué indica la ficha del Intergard 475HS de International sobre los primeros auxilios en caso de inhalación?

**Comportamiento esperado:** Reconocer que no hay evidencia suficiente: el Intergard 475HS no está entre las 101 fichas del corpus (hay otros productos de International/AkzoNobel, pero no ese). No debe atribuirle los primeros auxilios de otro producto.

**topk3 (top-k 3)** — el sistema NO dijo que no hay evidencia

> Según la ficha del Intergard 475HS de International [1], en caso de inhalación se debe enjuagar los ojos inmediatamente con mucha agua, levantando de vez en cuando los párpados superior e inferior. Verificar si la víctima lleva lentes de contacto y en este caso, retirárselas. Continúe enjuagando por lo menos durante 10 minutos. Procurar atención médica. Transportar a la víctima al exterior y mantenerla en reposo en una posición confortable para respirar. Si no hay respiración, ésta es irregular u ocurre un paro respiratorio, el personal capacitado debe proporcionar respiración artificial u oxígeno.

Fragmentos recuperados: [1] fds084-zinc-primer-10844-gris-parte-a-international-aksonobel · pág. 2 · sección 4; [2] fds082-acrilica-mantenimiento-13883-blanco-ral9003-brillante-intern · pág. 2 · sección 4; [3] fds095-international-aksonobel-sealer-f100-parte-a · pág. 3 · sección 4

- Fuentes que listó el sistema: [1] AkzoNobel · X International. · versión 1 · FDS 84 - ZINC PRIMER 10844 GRIS PARTE A - INTERNATIONAL - AKSONOBEL.pdf · pág. 2 · sección 4 Primeros auxilios
- **Revisión del autor** — ¿reconoce la falta de evidencia o inventa?  ☐ reconoce  ☐ inventa  ☐ parcial
- Observaciones: 

**topk6 (top-k 6)** — el sistema NO dijo que no hay evidencia

> Enjuague los ojos inmediatamente con mucha agua, levantando de vez en cuando los párpados superior e inferior. Verifique si la víctima lleva lentes de contacto y en este caso, retire los lentes. Continúe enjuagando por lo menos durante 10 minutos. Procure atención médica. Transporte a la víctima al exterior y manténgala en reposo en una posición cómoda para respirar. Si se sospecha que los vapores continúan presentes, el personal encargado del rescate deberá usar una máscara adecuada o un aparato de respiración autónoma. Si no hay respiración, ésta es irregular u ocurre un paro respiratorio, el personal capacitado debe proporcionar respiración artificial u oxígeno. [1]

Fragmentos recuperados: [1] fds084-zinc-primer-10844-gris-parte-a-international-aksonobel · pág. 2 · sección 4; [2] fds082-acrilica-mantenimiento-13883-blanco-ral9003-brillante-intern · pág. 2 · sección 4; [3] fds095-international-aksonobel-sealer-f100-parte-a · pág. 3 · sección 4; [4] fds085-epoxy-estructuras-gris-parte-a-international-aksonobel · pág. 2 · sección 4; [5] fds098-epoxy-zinc-plus-primer-10073-plus-gris-parte-a-international · pág. 3 · sección 4; [6] fds083-epoxy-zinc-primer-10056 · pág. 2 · sección 4

- Fuentes que listó el sistema: [1] AkzoNobel · X International. · versión 1 · FDS 84 - ZINC PRIMER 10844 GRIS PARTE A - INTERNATIONAL - AKSONOBEL.pdf · pág. 2 · sección 4 Primeros auxilios
- **Revisión del autor** — ¿reconoce la falta de evidencia o inventa?  ☐ reconoce  ☐ inventa  ☐ parcial
- Observaciones: 

## B. Casos respondibles (menor puntuación)

### e04 — directa (secciones [3])

**Pregunta:** ¿Qué porcentaje de dióxido de titanio contiene el Sigmadur One Buff 3142 de PPG y cuál es su número CAS?

**Referencia:** El Sigmadur One Buff 3142 contiene dióxido de titanio en una concentración de 7 - <10 % y su número CAS es 13463-67-7.

Evidencia de la referencia:
- FDS 65 - SIGMADUR ONE BUFF 3142 - PPG.pdf · pág. 3 · sección 3 Composición / información sobre los componentes: «Dióxido de titanio 7 - <10 13463-67-7»

| Config | Faithfulness | Context Precision | Context Recall | Errores del evaluador |
|---|---|---|---|---|
| topk3 | 0.50 | 1.00 | 1.00 | — |
| topk6 | 0.50 | 1.00 | 1.00 | — |

#### topk3 (top-k 3)

> El Sigmadur One Buff 3142 de PPG contiene un porcentaje de dióxido de titanio de 7 - <10%. Su número CAS es 13463-67-7 [1].

Fragmentos recuperados, en orden: [1] fds065-sigmadur-one-buff-3142-ppg · pág. 3 · sección 3; [2] fds065-sigmadur-one-buff-3142-ppg · pág. 3 · sección 3; [3] fds065-sigmadur-one-buff-3142-ppg · pág. 13 · sección 11

Pre-chequeo automático de cada cita (¿los números de la afirmación están en el fragmento citado?):

- [1] «El Sigmadur One Buff 3142 de PPG contiene un porcentaje de dióxido de titanio de 7 - <10%. Su número CAS es 13…» → los números aparecen en el fragmento

- **Revisión del autor** — exactitud de la respuesta:  ☐ correcta  ☐ parcial  ☐ incorrecta
- Citas (cada [n] apunta a la página y sección correctas del PDF):  ☐ todas  ☐ algunas incorrectas  ☐ ninguna
- Observaciones: 

#### topk6 (top-k 6)

> El Sigmadur One Buff 3142 de PPG contiene un porcentaje de dióxido de titanio de 7 - <10% [1], y su número CAS es 13463-67-7 [1].

Fragmentos recuperados, en orden: [1] fds065-sigmadur-one-buff-3142-ppg · pág. 3 · sección 3; [2] fds065-sigmadur-one-buff-3142-ppg · pág. 3 · sección 3; [3] fds065-sigmadur-one-buff-3142-ppg · pág. 13 · sección 11; [4] fds065-sigmadur-one-buff-3142-ppg · pág. 6 · sección 8; [5] fds065-sigmadur-one-buff-3142-ppg · pág. 13 · sección 11; [6] fds065-sigmadur-one-buff-3142-ppg · pág. 10 · sección 11

Pre-chequeo automático de cada cita (¿los números de la afirmación están en el fragmento citado?):

- [1] «El Sigmadur One Buff 3142 de PPG contiene un porcentaje de dióxido de titanio de 7 - <10%…» → los números aparecen en el fragmento
- [1] «, y su número CAS es 13463-67-7…» → los números aparecen en el fragmento

Pasos internos de Faithfulness (el evaluador genera las afirmaciones en inglés):

- [1] The Sigmadur One Buff 3142 of PPG contains a percentage of titanium dioxide of 7 - <10% — The context explicitly mentions the composition of the Sigmadur One Buff 3142, including the percentage of titanium dioxide, which is 7 - <10%. Therefore, this statement can be directly inferred.
- [0] The CAS number of the Sigmadur One Buff 3142 of PPG is 13463-67-7 — The context mentions the CAS number of Dióxido de titanio as 13463-67-7, but it does not explicitly mention the CAS number of the Sigmadur One Buff 3142. Therefore, this statement cannot be directly inferred.

- **Revisión del autor** — exactitud de la respuesta:  ☐ correcta  ☐ parcial  ☐ incorrecta
- Citas (cada [n] apunta a la página y sección correctas del PDF):  ☐ todas  ☐ algunas incorrectas  ☐ ninguna
- Observaciones: 

### e07 — comparativa_versiones (secciones [7, 9])

**Pregunta:** Compara la ficha de 2019 y la de 2021 de la Pintura Primera Mano & Acabado de Corona: ¿cómo cambian el tiempo máximo de almacenamiento y la densidad a 20 ºC?

**Referencia:** En la ficha de 2019 (versión 1, emisión 05/06/2019) el tiempo máximo de almacenamiento es de 36 meses y la densidad a 20 ºC es 1371,4 kg/m³ (relativa 1,371). En la ficha de 2021 (versión 3, que sustituye a la 2; revisión 24/11/2021) el tiempo máximo es de 12 meses y la densidad es 1377,5 kg/m³ (relativa 1,377). Es decir, el tiempo máximo de almacenamiento bajó de 36 a 12 meses y la densidad aumentó ligeramente.

Evidencia de la referencia:
- FDS 29 - PINTURA PRIMERA MANO & ACABADO - CORONA .pdf · pág. 3 · sección 7 Manipulación y almacenamiento (7.2): «Tiempo máximo: 36 meses»
- FDS 29 - PINTURA PRIMERA MANO & ACABADO - CORONA .pdf · pág. 5 · sección 9 Propiedades físicas y químicas: «Densidad a 20 ºC: 1371,4 kg/m³»
- FDS 43 - PINTURA PRIMERA MANO & ACABADO - CORONA .pdf · pág. 3 · sección 7 Manipulación y almacenamiento (7.2): «Tiempo máximo: 12 meses»
- FDS 43 - PINTURA PRIMERA MANO & ACABADO - CORONA .pdf · pág. 5 · sección 9 Propiedades físicas y químicas: «Densidad a 20 ºC: 1377,5 kg/m³»

| Config | Faithfulness | Context Precision | Context Recall | Errores del evaluador |
|---|---|---|---|---|
| topk3 | 0.75 | 1.00 | 0.60 | — |
| topk6 | 0.50 | 1.00 | 1.00 | — |

#### topk3 (top-k 3)

> El tiempo máximo de almacenamiento en la versión 2019 es de 36 meses [2], mientras que en la versión 2021 se reduce a 12 meses [1].  La densidad a 20 ºC es de 1377,5 kg/m³ en la versión 2021 [3], no se menciona esta información en la versión 2019 [2].

Fragmentos recuperados, en orden: [1] fds043-pintura-primera-mano-acabado-corona · pág. 3-4 · sección 7; [2] fds029-pintura-primera-mano-acabado-corona · pág. 3-4 · sección 7; [3] fds043-pintura-primera-mano-acabado-corona · pág. 5 · sección 9

Pre-chequeo automático de cada cita (¿los números de la afirmación están en el fragmento citado?):

- [2] «El tiempo máximo de almacenamiento en la versión 2019 es de 36 meses…» → los números aparecen en el fragmento
- [1] «, mientras que en la versión 2021 se reduce a 12 meses…» → los números aparecen en el fragmento
- [3] «.

La densidad a 20 ºC es de 1377,5 kg/m³ en la versión 2021…» → los números aparecen en el fragmento
- [2] «, no se menciona esta información en la versión 2019…» → los números aparecen en el fragmento

Pasos internos de Faithfulness (el evaluador genera las afirmaciones en inglés):

- [1] The storage time in the 2019 version is 36 months. — The context explicitly mentions that the storage time in the 2019 version is 36 months.
- [1] The storage time in the 2021 version is 12 months. — The context explicitly mentions that the storage time in the 2021 version is 12 months.
- [1] The density at 20 degrees Celsius in the 2021 version is 1377.5 kg/m^3. — The context explicitly mentions that the density at 20 degrees Celsius in the 2021 version is 1377.5 kg/m^3.
- [0] The density at 20 degrees Celsius is not mentioned in the 2019 version. — The context does not mention the density at 20 degrees Celsius in the 2019 version, but it does mention that the density at 20 degrees Celsius in the 2021 version is 1377.5 kg/m^3. However, it does not explicitly state t

- **Revisión del autor** — exactitud de la respuesta:  ☐ correcta  ☐ parcial  ☐ incorrecta
- Citas (cada [n] apunta a la página y sección correctas del PDF):  ☐ todas  ☐ algunas incorrectas  ☐ ninguna
- Observaciones: 

#### topk6 (top-k 6)

> El tiempo máximo de almacenamiento cambia de 36 meses en la versión 1 de 2019 [2] a 12 meses en la versión 3 de 2021 [1]. La densidad a 20 ºC es de 1377,5 kg/m³ en la versión 3 de 2021 [3], mientras que en la versión 1 de 2019 [4] es de 1371,4 kg/m³.

Fragmentos recuperados, en orden: [1] fds043-pintura-primera-mano-acabado-corona · pág. 3-4 · sección 7; [2] fds029-pintura-primera-mano-acabado-corona · pág. 3-4 · sección 7; [3] fds043-pintura-primera-mano-acabado-corona · pág. 5 · sección 9; [4] fds029-pintura-primera-mano-acabado-corona · pág. 5 · sección 9; [5] fds043-pintura-primera-mano-acabado-corona · pág. 5-6 · sección 9; [6] fds029-pintura-primera-mano-acabado-corona · pág. 5 · sección 9

Pre-chequeo automático de cada cita (¿los números de la afirmación están en el fragmento citado?):

- [2] «El tiempo máximo de almacenamiento cambia de 36 meses en la versión 1 de 2019…» → los números aparecen en el fragmento
- [1] «a 12 meses en la versión 3 de 2021…» → los números aparecen en el fragmento
- [3] «. La densidad a 20 ºC es de 1377,5 kg/m³ en la versión 3 de 2021…» → los números aparecen en el fragmento
- [4] «, mientras que en la versión 1 de 2019…» → los números aparecen en el fragmento

Pasos internos de Faithfulness (el evaluador genera las afirmaciones en inglés):

- [0] The maximum storage time changes from 36 months in the 2019 version to 12 months in the 2021 version. — The context mentions that the maximum storage time is 12 months for the 2021 version, but it does not provide information about the 2019 version. Therefore, it cannot be deduced that the maximum storage time changes from
- [1] The density at 20 degrees Celsius is 1377.5 kg/m^3 in the 2021 version, while in the 2019 version it is 1371.4 kg/m^3. — The context explicitly mentions the density at 20 degrees Celsius for both the 2021 and 2019 versions, so it can be deduced that the statement is true.

- **Revisión del autor** — exactitud de la respuesta:  ☐ correcta  ☐ parcial  ☐ incorrecta
- Citas (cada [n] apunta a la página y sección correctas del PDF):  ☐ todas  ☐ algunas incorrectas  ☐ ninguna
- Observaciones: 

### e09 — comparativa_productos (secciones [2])

**Pregunta:** Compara la Pintulaca Rojo Claro 7587 y el Esmalte Top Quality Negro 1772 de Pintuco: ¿cuál está clasificado por toxicidad para la reproducción y qué categoría de líquido inflamable tiene cada uno?

**Referencia:** La Pintulaca Rojo Claro 7587 está clasificada como tóxica para la reproducción categoría 1A (Repr. 1A, H360: puede perjudicar la fertilidad o dañar al feto) y como líquido inflamable categoría 2 (H225). El Esmalte Top Quality Negro 1772 no tiene clasificación de toxicidad para la reproducción en su sección 2 y es líquido inflamable categoría 3 (Liq. Infl. 3, H226: líquido y vapores inflamables).

Evidencia de la referencia:
- FDS 34 - PINTULACA ROJO CLARO 7587 - PINTUCO .pdf · pág. 1 · sección 2 Identificación de peligros: «Repr. 1A: H360 - Puede perjudicar la fertilidad o dañar al feto»
- FDS 34 - PINTULACA ROJO CLARO 7587 - PINTUCO .pdf · pág. 1 · sección 2 Identificación de peligros: «Liq. Infl. 2: H225 - Líquido y vapores muy inflamables»
- FDS 35- ESMALTE TOP QUALITY NEGRO 1772 - PINTUCO .pdf · pág. 1 · sección 2 Identificación de peligros: «Liq. Infl. 3: H226 - Líquido y vapores inflamables»

| Config | Faithfulness | Context Precision | Context Recall | Errores del evaluador |
|---|---|---|---|---|
| topk3 | 1.00 | 1.00 | 1.00 | — |
| topk6 | 0.67 | 1.00 | NaN | context_recall: RagasOutputParserException: The output parser failed to parse the output including retries. |

#### topk3 (top-k 3)

> No hay evidencia suficiente en las FDS disponibles para determinar si la Pintulaca Rojo Claro 7587 o el Esmalte Top Quality Negro 1772 de Pintuco están clasificados por toxicidad para la reproducción. Ambos productos indican que no se cumplen los criterios de clasificación para esta categoría [1][3].

Fragmentos recuperados, en orden: [1] fds035-esmalte-top-quality-negro-1772-pintuco · pág. 7 · sección 11; [2] fds030-esmalte-top-quality-gris-plata-1799-pintuco · pág. 7 · sección 11; [3] fds038-esmalte-top-quality-rojo-bermellon-9409-pintuco · pág. 7 · sección 11

Pre-chequeo automático de cada cita (¿los números de la afirmación están en el fragmento citado?):

- [1] «No hay evidencia suficiente en las FDS disponibles para determinar si la Pintulaca Rojo Claro 7587 o el Esmalt…» → FALTAN números en el fragmento (7587)
- [3] «No hay evidencia suficiente en las FDS disponibles para determinar si la Pintulaca Rojo Claro 7587 o el Esmalt…» → FALTAN números en el fragmento (7587, 1772)

- **Revisión del autor** — exactitud de la respuesta:  ☐ correcta  ☐ parcial  ☐ incorrecta
- Citas (cada [n] apunta a la página y sección correctas del PDF):  ☐ todas  ☐ algunas incorrectas  ☐ ninguna
- Observaciones: 

#### topk6 (top-k 6)

> El Pintulaca Rojo Claro 7587 está clasificado por toxicidad para la reproducción, ya que puede perjudicar la fertilidad o dañar al feto [5]. Por otro lado, el Esmalte Top Quality Negro 1772 no está clasificado por toxicidad para la reproducción [1][2][3][4][6].

Fragmentos recuperados, en orden: [1] fds035-esmalte-top-quality-negro-1772-pintuco · pág. 7 · sección 11; [2] fds030-esmalte-top-quality-gris-plata-1799-pintuco · pág. 7 · sección 11; [3] fds038-esmalte-top-quality-rojo-bermellon-9409-pintuco · pág. 7 · sección 11; [4] fds033-esmalte-top-quality-azul-medio-1795-pintuco · pág. 7 · sección 11; [5] fds034-pintulaca-rojo-claro-7587-pintuco · pág. 8 · sección 11; [6] fds032-pintulaca-blanco-7519-pintuco · pág. 7-8 · sección 11

Pre-chequeo automático de cada cita (¿los números de la afirmación están en el fragmento citado?):

- [5] «El Pintulaca Rojo Claro 7587 está clasificado por toxicidad para la reproducción, ya que puede perjudicar la f…» → los números aparecen en el fragmento
- [1] «. Por otro lado, el Esmalte Top Quality Negro 1772 no está clasificado por toxicidad para la reproducción…» → los números aparecen en el fragmento
- [2] «. Por otro lado, el Esmalte Top Quality Negro 1772 no está clasificado por toxicidad para la reproducción…» → FALTAN números en el fragmento (1772)
- [3] «. Por otro lado, el Esmalte Top Quality Negro 1772 no está clasificado por toxicidad para la reproducción…» → FALTAN números en el fragmento (1772)
- [4] «. Por otro lado, el Esmalte Top Quality Negro 1772 no está clasificado por toxicidad para la reproducción…» → FALTAN números en el fragmento (1772)
- [6] «. Por otro lado, el Esmalte Top Quality Negro 1772 no está clasificado por toxicidad para la reproducción…» → FALTAN números en el fragmento (1772)

Pasos internos de Faithfulness (el evaluador genera las afirmaciones en inglés):

- [1] The Pintulaca Rojo Claro 7587 is classified by toxicity for reproduction. — The context mentions that the Pintulaca Rojo Claro 7587 can harm fertility or damage the fetus, which implies that it is classified by toxicity for reproduction.
- [1] The Pintulaca Rojo Claro 7587 can harm fertility or damage the fetus. — The context explicitly states that the Pintulaca Rojo Claro 7587 can harm fertility or damage the fetus.
- [1] The Esmalte Top Quality Negro 1772 is not classified by toxicity for reproduction. — The context does not mention the Esmalte Top Quality Negro 1772 being classified by toxicity for reproduction, but it does mention that it does not present substances classified as harmful with sensitizing effects, which

- **Revisión del autor** — exactitud de la respuesta:  ☐ correcta  ☐ parcial  ☐ incorrecta
- Citas (cada [n] apunta a la página y sección correctas del PDF):  ☐ todas  ☐ algunas incorrectas  ☐ ninguna
- Observaciones: 
