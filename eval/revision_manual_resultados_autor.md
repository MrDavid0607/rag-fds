# Resultados de la revisión manual del autor (5 casos) — 2026-11-17

Registro exportado por el autor desde `eval/revision_manual/index.html`: `eval/revision_manual_autor.json`. Aquí se transcribe **tal cual** y se contrasta con la revisión asistida por IA (`eval/revision_asistida_ia.md`).
El autor no escribió observaciones y solo marcó la correspondencia de las citas en un caso (e09, top-k 3); en los demás casos la casilla de citas quedó **sin marcar** (no hay dato del autor sobre ellas).

| Caso | Config | Exactitud (autor) | Citas (autor) | Revisión asistida por IA | Coincide |
|---|---|---|---|---|---|
| e11 (sin respuesta, Acrolatex) | top-k 3 | correcta | — | reconoce la falta de evidencia | ✅ |
| e11 | top-k 6 | correcta | — | reconoce la falta de evidencia | ✅ |
| e12 (sin respuesta, Intergard) | top-k 3 | correcta | — | reconoce (v2) | ✅ |
| e12 | top-k 6 | correcta | — | reconoce (v2) | ✅ |
| e04 (Sigmadur) | top-k 3 | correcta | — | correcta, citas correctas | ✅ |
| e04 | top-k 6 | **parcial** | — | correcta, citas correctas | ⚠️ difieren |
| e07 (versiones Corona) | top-k 3 | parcial | — | parcial (afirmación falsa sobre 2019) | ✅ |
| e07 | top-k 6 | **parcial** | — | correcta, las 4 citas correctas | ⚠️ difieren |
| e09 (Rojo Claro vs Top Quality Negro) | top-k 3 | incorrecta | **todas correctas** | incorrecta; cita [3] de otra ficha (FDS 38) | exactitud ✅ · citas ⚠️ difieren |
| e09 | top-k 6 | **incorrecta** | — | parcial (correcta pero incompleta; 4 de 5 citas de la 2.ª afirmación son de otras fichas) | ⚠️ difieren |

## Lectura
- **Coinciden** en e11, e12, e04 top-k 3, e07 top-k 3 y en la exactitud de e09 top-k 3.
- **Difieren** en 4 de los 10 bloques de exactitud (e04 top-k 6, e07 top-k 6, e09 top-k 6) y en las citas de e09 top-k 3. Sin observaciones del autor no se sabe en qué se basó cada marca; posibles causas: criterio más estricto con la completitud (p. ej. que e07 top-k 6 no explique «versión» frente a año, o que e04 no aclare que el CAS es del dióxido de titanio) o una lectura distinta de las citas.
- **La valoración del autor es la que se usa como referencia humana** en el informe; la revisión asistida por IA se conserva como segunda lectura. Las discrepancias quedan abiertas hasta que el autor las precise.
- En e09 top-k 3, el autor marcó «todas correctas», pero uno de los fragmentos citados ([3]) es de otra ficha (FDS 38, esmalte rojo bermellón): conviene que el autor lo revise antes de sustentar.
