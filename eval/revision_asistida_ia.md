# Revisión asistida por IA de los 5 casos (Fase 7)

**Qué es esto y qué no es.** Revisión hecha por Claude (el asistente) comparando cada respuesta y cada cita con el **texto del PDF** (capa de texto, comprobada línea por línea) y, en algunos casos, con la imagen de la página.
**No es la verificación del autor**: las casillas de `eval/revision_manual.md` y de `eval/revision_manual/index.html` siguen vacías. El autor debe, como mínimo, comprobar por sí mismo los puntos marcados con ⚑ para poder explicarlos en la demostración.

Fecha: 2026-11-17 · Datos: corrida v2 (idéntica a v1 en estos casos).

| Caso | top-k 3 | top-k 6 |
|---|---|---|
| e04 | **Correcta** · citas correctas | **Correcta** · citas correctas |
| e07 | **Parcial** (afirmación falsa sobre 2019) · citas [1][2][3] correctas | **Correcta** · las 4 citas correctas |
| e09 | **Incorrecta** (atribuye al Pintulaca Rojo Claro lo que dice otra ficha) · cita [3] de otra ficha | **Parcial** (lo que dice es correcto, omite la inflamabilidad) · 4 de 5 citas de la 2.ª afirmación son de otras fichas |
| e11 | **Reconoce** la falta de evidencia | **Reconoce** la falta de evidencia |
| e12 | **Reconoce** (producto inexistente) | **Reconoce** (producto inexistente) |

## e04 — Sigmadur One Buff 3142 (PPG): % y CAS del dióxido de titanio
- **Dato en el PDF** (FDS 65, pág. 3, sección 3, tabla de composición): «Dióxido de titanio · 7 - <10 · 13463-67-7».
- **top-k 3 y top-k 6**: «7 - <10 %» y «CAS 13463-67-7» → **exactos**. La cita `[1]` es el fragmento de la pág. 3, sección 3 → **correcta** (página y sección).
- Observación: «su número CAS» no aclara que es el del dióxido de titanio (no del producto); por eso RAGAS puntúa Faithfulness 0.50, que refleja literalidad del evaluador y no un error de datos.

## e07 — Pintura Primera Mano & Acabado, Corona (FDS 29 de 2019 y FDS 43 de 2021)
- **Datos en el PDF**: FDS 29 pág. 3 «Tiempo máximo: 36 meses», pág. 5 «Densidad a 20 ºC: 1371,4 kg/m³», encabezado «Versión: 1»; FDS 43 pág. 3 «Tiempo máximo: 12 meses», pág. 5 «Densidad a 20 ºC: 1377,5 kg/m³», encabezado «Versión: 3 (sustituye a 2)».
- **top-k 6**: 36 → 12 meses, 1377,5 y 1371,4 kg/m³, «versión 1 de 2019», «versión 3 de 2021» → **todo exacto**. Citas: [2] FDS 29 págs. 3-4 §7 ✓, [1] FDS 43 págs. 3-4 §7 ✓, [3] FDS 43 pág. 5 §9 ✓, [4] FDS 29 pág. 5 §9 ✓ → **todas correctas**. RAGAS le da Faithfulness 0.50 porque su evaluador declaró no respaldada la comparación 36 → 12 meses aunque ambos datos están en los contextos [1] y [2]: falso negativo del evaluador.
- **top-k 3**: 36 meses ✓, 12 meses ✓ y 1377,5 kg/m³ ✓, **pero afirma que «no se menciona [la densidad] en la versión 2019 [2]» y es falso** (FDS 29, pág. 5, §9: 1371,4 kg/m³). El fragmento de la densidad de 2019 no se recuperó con k = 3. La cita [2] respalda lo de 36 meses pero no esa frase.

## e09 — Pintulaca Rojo Claro 7587 vs Esmalte Top Quality Negro 1772 (Pintuco): toxicidad para la reproducción y categoría de inflamabilidad
- **Datos en el PDF** (verificados en el texto y, para la FDS 35 pág. 1, con la imagen de la página):
  FDS 34 pág. 1 §2: «Repr. 1A: H360 - Puede perjudicar la fertilidad o dañar al feto» y «Liq. Infl. 2: H225»; pág. 8 §11: «Toxicidad para la reproducción: Puede perjudicar la fertilidad o dañar al feto».
  FDS 35 pág. 1 §2: clasificación Acuático agudo 3 (H402), Acuático crónico 3 (H412), Irrit. Cut. 2, **Liq. Infl. 3 (H226)**, Sens. Cut. 1A, STOT única 3, Tox. Asp. 1 (H304) → **no hay Repr.**; pág. 7 §11: «Toxicidad para la reproducción: …no se cumplen los criterios de clasificación».
- **top-k 6**: «El Pintulaca Rojo Claro 7587 está clasificado por toxicidad para la reproducción… [5]» → **exacto**; [5] = FDS 34 pág. 8 §11 ✓. «El Top Quality Negro 1772 no está clasificado… [1][2][3][4][6]» → **cierto para la ficha 35**, pero de las 5 citas solo [1] (FDS 35 pág. 7 §11) es de ese producto: **[2] es FDS 30 (gris plata), [3] FDS 38 (rojo bermellón), [4] FDS 33 (azul medio) y [6] FDS 32 (Pintulaca Blanco) → citas a otras fichas** (⚑). **Omite la categoría de líquido inflamable** (parte de la pregunta; correcta: Pintulaca Rojo Claro cat. 2 H225; Top Quality Negro cat. 3 H226) → respuesta **incompleta**.
- **top-k 3**: los tres fragmentos recuperados son de FDS 35, 30 y 38 (**ninguno de la ficha 34**). Dice «No hay evidencia suficiente…» y a continuación afirma que «ambos productos» no cumplen los criterios de clasificación, citando [1][3]: **falso para el Pintulaca Rojo Claro** (sí tiene Repr. 1A, H360) y **[3] es de otra ficha** (FDS 38). No responde la inflamabilidad. → respuesta **incorrecta** (⚑).
- Por qué sale mal (ver `eval/analisis_resultados.md` §3.A): el filtro de producto deja 6 productos candidatos y el tema «toxicidad para la reproducción» sugiere la sección 11, mientras que la clasificación (H360, H225/H226) está en la sección 2.

## e11 — Rendimiento teórico del Acrolatex 50 3508 (no está en la FDS)
- Búsqueda en el texto de las 10 páginas de la FDS 57: no aparecen «rendimiento», «m²/galón», «cobertura» ni «rinde». Ambas configuraciones responden «No hay evidencia suficiente en las FDS disponibles para…» y no listan fuentes → **reconocen la falta de evidencia, sin inventar**.

## e12 — Intergard 475HS de International (producto que no está en el corpus)
- Búsqueda de «intergard» y «475HS» en el texto de los 101 PDF: sin coincidencias → el producto no existe en el corpus.
- v2, ambas configuraciones: «No hay evidencia suficiente… para el Intergard 475HS de International, ya que los fragmentos corresponden a otros productos de AkzoNobel»; sin fuentes → **reconoce**.
- En v1 (antes de corregir los nombres de producto de 8 fichas) **inventaba** con primeros auxilios de la FDS 84. El cambio es frágil (ver el análisis): el filtro de producto y el aviso de variante siguen sin activarse en este caso.

## Límites de esta revisión
- Verificación sobre el **texto** de los PDF; solo se miró la **imagen** de la página en FDS 35 pág. 1 (e09), FDS 31 págs. 2 y 5 (extracción) y las páginas de apoyo de `eval/revision_preguntas/`.
- Las exactitudes aquí son del asistente; que las respuestas «parecen correctas» no sustituye la comprobación del autor, que es la que pide la guía.
