# RAG con Fichas de Datos de Seguridad (FDS)

Parcial final de Procesamiento de Lenguaje Natural — Universidad Sergio Arboleda, 2026 S02.

**Autores:** Daniel Reyes, Sebastián Urrego y David Martínez.
**Repositorio (público):** <https://github.com/MrDavid0607/rag-fds> · Los PDF originales **no** se incluyen (`data/raw/` está en `.gitignore`): para reproducir, ponlos en `data/raw/FDS EVALUADAS/` conservando las carpetas por año.

Sistema RAG (recuperación aumentada por generación) sobre **101 Fichas de Datos de Seguridad** del sector de pinturas (1 134 páginas, 8 fabricantes,
carpetas por año 2018-2025). Convierte los PDF a Markdown con trazabilidad de página, responde con **citas verificables** (fabricante · producto · versión ·
documento · página · sección), avisa cuando la evidencia no alcanza y se evalúa con RAGAS usando únicamente modelos locales de Ollama. **No usa ninguna API de pago.**

## Mapa rápido para el revisor

| Quiero ver… | Dónde |
|---|---|
| Qué pide la guía y dónde está cada cosa (con estados honestos) | [`docs/cumplimiento_guia.md`](docs/cumplimiento_guia.md) |
| El informe de 2 páginas | [`informe/informe.pdf`](informe/informe.pdf) · guion de la demostración: [`informe/guion_demo.md`](informe/guion_demo.md) |
| Las FDS convertidas a Markdown (con página, imágenes y metadatos) | `data/processed/<doc_id>/` |
| La verificación de la extracción y sus errores | `verificacion/` (`errores_extraccion.md`, `secciones.csv`, `verificacion_extraccion.csv`, `revision_asistida_ia.md`) |
| Las 12 preguntas, resultados top-k 3 vs 6 y su análisis | `eval/` (`preguntas.json`, `resultados_topk{3,6}.csv`, `resumen.csv`, `analisis_resultados.md`) |
| Cómo funciona el RAG y sus parámetros | [`docs/rag_diseno.md`](docs/rag_diseno.md) · `config/` · `src/rag_fds/` |
| Hardware, tiempos y costo | `metricas/` |

**Ejecutar solo el RAG y la demo (sin los PDF ni la extracción):** los Markdown ya están en `data/processed/`. Instala `requirements-rag.txt`, baja `bge-m3` y `qwen2.5:7b-instruct` con Ollama, y corre `python -m rag_fds.chunking && python -m rag_fds.indice` (≈ 5 min) y luego `streamlit run app/demo.py` (ver §2, pasos 4 y 5). El índice no se sube al repositorio porque se regenera.
Las FDS son documentos de sus fabricantes (Pintuco, Corona, PPG, Pintuland, INVESA, Sika, AkzoNobel/International, Bler y otros); se usan aquí solo con fines académicos.

## Avance

- [x] Fase 0 — Entorno, cuentas y plan
- [x] Fase 1 — Infraestructura en AWS (EC2 `r5.large` + Ollama); la inferencia se movió al PC con GPU (ver §1)
- [x] Fase 2 — Extracción PDF → Markdown (101 fichas)
- [x] Fase 3 — Secciones y verificación de la extracción (método mixto: comprobación automática de las 1 248 tablas + revisión asistida por IA + **verificación visual del autor en 24 fichas**: 13 coinciden y 11 con errores; ver `verificacion/errores_extraccion.md`)
- [x] Fase 4 — RAG con trazabilidad (funcional; el autor validó contra el PDF las citas de dos consultas de la demo el 2026-11-17: medios de extinción del Topcoat 400 1793, FDS 80 pág. 4, y la comparación de la Pintura Primera Mano & Acabado, FDS 29 y 43 págs. 3 y 5; coincidieron)
- [x] Fase 5 — 12 preguntas de evaluación (evidencia literal comprobada automáticamente contra el PDF; **verificadas por el autor el 2026-11-17**, registro exportado en `eval/verificacion_preguntas_autor.json`)
- [x] Fase 6 — Evaluación con RAGAS (top-k 3 vs 6; v1 y v2). Las referencias se verificaron después de la corrida y el autor las aprobó sin cambios, por lo que los resultados no se repitieron
- [x] Fase 7 — Revisión manual y análisis (revisión manual del autor de los 5 casos en `eval/revision_manual_resultados_autor.md`, contrastada con la revisión asistida por IA; hay discrepancias abiertas y el autor no marcó la correspondencia de citas salvo en un caso)
- [x] Fase 8 — Documentación, informe y cierre (README, informe de 2 páginas, guion de demo y barrido de credenciales hechos; la verificación humana cubre las 12 referencias, 24 fichas de la extracción y la exactitud de los 5 casos analizados; no se marcó la correspondencia de citas salvo en un caso)

## 1. Arquitectura

```
PC del autor (Windows 11, RTX 3050 de 4 GB, 16 GB RAM)                    AWS Learner Lab · us-east-1
──────────────────────────────────────────────────                        ─────────────────────────────
 Claude Code + repo git                                                    EC2 r5.large (2 vCPU, 16 GB)
 ├─ Docling (GPU): PDF → Markdown + imágenes + procedencia                 ├─ creada por CLI (infra/*.sh)
 ├─ Ollama 127.0.0.1:11434 (GPU)                                           ├─ Ollama + modelos probados
 │    bge-m3 (embeddings) · qwen2.5:7b-instruct (generador)                ├─ Docling en CPU (muestra de 5 fichas)
 │    llama3.1:8b (evaluador RAGAS)                                        └─ SSH solo desde la IP del autor (puerto 22);
 ├─ Chroma (índice persistente, 6 483 fragmentos)                              Ollama en 127.0.0.1, acceso por túnel SSH
 ├─ RAG (rag.py) · RAGAS (evaluacion.py)
 └─ Demo Streamlit en 127.0.0.1:8501
        │
        └─ git push ──► GitHub (cuenta MrDavid0607, repositorio privado)
```

**Decisión y justificación.** El plan inicial ponía todo en una EC2 `m5.2xlarge` (8 vCPU, 32 GB). La política del Learner Lab (`Pvoclabs2`) **deniega** `m5.2xlarge`,
`t3.2xlarge`, `m5.xlarge` y cualquier tamaño mayor a *large*; la más potente permitida fue `r5.large` (2 vCPU, 16 GB). Midiendo (ver `metricas/`):

| Tarea | EC2 `r5.large` (CPU) | PC con GPU RTX 3050 |
|---|---|---|
| Generación `qwen2.5:7b-instruct` | 1.7 tokens/s | 8.3 tokens/s (parcial en GPU) |
| Extracción Docling, mismas 5 fichas (61 págs.) | 1 048 s (17 s/pág.) | 143 s (2.4 s/pág., incluye carga de modelos) |

Con la EC2 el corpus completo habría tardado ≈ 5 h en extraerse y RAGAS habría sido inviable. Por eso **la extracción, el índice, la generación y la evaluación corren en el PC**; la EC2
quedó para la infraestructura reproducible por CLI y las pruebas iniciales, y se mantiene **detenida**. Compromiso: se pierde simplicidad de «todo en la nube» a cambio de desempeño (≈ 7× en extracción, ≈ 5× en generación)
y de costo AWS prácticamente nulo; la reproducción requiere GPU local (o paciencia en CPU). SageMaker no se usó: la guía no lo exige y añadiría complejidad.

## 2. Reproducirlo de cero

Requisitos: Python 3.13, [Ollama](https://ollama.com), GPU NVIDIA con CUDA 12.8 (opcional; en CPU todo funciona más lento) y los 101 PDF en `data/raw/FDS EVALUADAS/` (no se suben al repositorio).

```bash
# 1. Entorno
python -m venv .venv && .venv\Scripts\activate
pip install torch==2.11.0 torchvision --index-url https://download.pytorch.org/whl/cu128   # (o la variante CPU)
pip install -r requirements.txt
set PYTHONPATH=src

# 2. Modelos locales (Ollama)
ollama pull bge-m3 && ollama pull qwen2.5:7b-instruct && ollama pull llama3.1:8b

# 3. Extracción PDF → Markdown, metadatos, secciones y verificación (Fases 2-3)
python -m rag_fds.extraccion --entrada "data/raw/FDS EVALUADAS" --salida data/processed
python -m rag_fds.metadatos
python -m rag_fds.secciones
python -m rag_fds.verificacion          # genera verificacion/revision/ (para la revisión manual)

# 4. Chunking e índice (Fase 4)
python -m rag_fds.chunking && python -m rag_fds.indice

# 5. Consultar
python -m rag_fds.rag "¿Qué medios de extinción son adecuados para el Topcoat 400 1793 Blanco?" --config config/topk6.yaml
streamlit run app/demo.py --server.address 127.0.0.1 --server.port 8501

# 6. Evaluación (Fases 5-6; solo preguntas con "verificada": true)
python -m rag_fds.validar_preguntas
powershell -File scripts\correr_evaluacion.ps1      # genera, puntúa con RAGAS y resume (≈ 90 min)
```

**AWS (opcional, Fase 1)**: con credenciales del Learner Lab en el perfil `[academy]`, desde Git Bash: `bash infra/crear.sh` (llave SSH fuera del repo, Security Group solo con el puerto 22 abierto a tu IP, EC2),
`infra/iniciar.sh`, `infra/ssh.sh`, `infra/tunel.sh` (Ollama de la EC2 en `localhost:11435`), `infra/sync_subir.sh`/`sync_bajar.sh` (con `tar` sobre SSH; Windows no trae `rsync`),
`infra/detener.sh`. La IP pública se consulta por tag en cada arranque; nunca se escribe fija.

## 3. Modelos y versiones

| Rol | Modelo | Digest (sha256, abreviado) |
|---|---|---|
| Embeddings | `bge-m3` (1 024 dim, F16) | `790764642607…` |
| Generador | `qwen2.5:7b-instruct` (Q4_K_M), temperatura 0, semilla 42, `num_ctx` 8 192 | `845dbda0ea48…` |
| Evaluador RAGAS | `llama3.1:8b` (Q4_K_M), temperatura 0, semilla 42, `num_ctx` 8 192, salida JSON | `46e0c10c039e…` |

Herramientas: Docling 2.150.1 (RapidOCR 3.10.0), Chroma 1.5.9, RAGAS 0.4.4, langchain 1.5.0 / langchain-ollama 1.1.0, Ollama 0.40.16, PyTorch 2.11.0+cu128. Todas las dependencias están fijadas en `requirements.txt`.
El generador y el evaluador son **distintos** para reducir el sesgo de autoevaluación.

## 4. Decisiones de diseño (resumen; detalle en `docs/rag_diseno.md`)

- **Extracción (Docling).** Tablas con estructura, imágenes recortadas por ficha (los logos repetidos se guardan una sola vez), marcas `<!-- pagina: N -->`, `meta.json` con sha256, página y herramienta. Los datos de contenido (fabricante, producto, versión, fecha)
  se toman del texto del PDF con su evidencia y **nunca se infieren**: si no aparecen quedan vacíos (15 fichas sin fabricante, 17 sin versión).
- **Secciones.** Las 16 secciones se identifican por su **título** (las FDS antiguas numeran distinto). Resultado: 1 612 presentes, 4 fallos de extracción, 0 ausentes; nada se completa por inferencia.
- **Chunking.** Por sección y luego por tamaño: ~800 caracteres con 150 de solapamiento, sin partir tablas (máx. 1 500 caracteres; si no, por filas repitiendo el encabezado). 6 483 fragmentos; cada uno lleva fabricante · producto · versión · año · sección y metadatos (documento, páginas, sección, imágenes de las mismas páginas).
- **Recuperación.** Filtros por fabricante, año y producto detectados en la pregunta *antes* de buscar; en comparaciones se recupera por producto o documento; un pequeño bonus favorece la sección que sugiere el tema.
- **Generación.** Prompt fijo en `config/base.yaml`; el modelo cita `[n]` y **el código construye la lista de fuentes** y marca citas inexistentes; si no hay evidencia debe decirlo.
- **Evaluación.** `config/topk3.yaml` y `config/topk6.yaml` heredan `base.yaml` y solo cambian `top_k` (comprobado por código). Preguntas de desarrollo distintas a las 12 de evaluación; las referencias viven solo en `eval/`.

## 5. Resultados

Evaluación con RAGAS sobre las 10 preguntas respondibles (`eval/resumen.csv`):

| Configuración | Faithfulness | Context Precision | Context Recall | Casos válidos F / CP / CR |
|---|---|---|---|---|
| top-k 3 | 0.892 | 1.000 | 0.910 | 10 / 10 / 10 |
| top-k 6 | 0.867 | 1.000 | 1.000 | 10 / 10 / 9 |

Un cálculo falló (Context Recall de e09 con top-k 6, `RagasOutputParserException`) y se registró como `NaN`, no como 0. **Estas puntuaciones orientan la comparación y requieren revisión manual; con 12 preguntas el conjunto
permite una comparación didáctica, no demuestra que una configuración sea mejor en general.** Análisis completo, errores por causa y configuración elegida (top-k 6): `eval/analisis_resultados.md`.

**Dos versiones de la evaluación.** v1 detectó que 8 fichas AkzoNobel tenían el nombre de producto mal extraído («X International.») y que e12 (producto inexistente) **inventaba** en ambas configuraciones. Se corrigieron los metadatos, se reconstruyó el índice y se repitió la evaluación (v2): las 11 preguntas restantes recuperaron lo mismo y las 30 puntuaciones salieron idénticas; solo e12 pasó a reconocer la falta de evidencia (resultado frágil, ver el análisis). La tabla de arriba es v2 (idéntica a v1); los datos de v1 están en `eval/v1_antes_correccion_metadatos/`.

## 6. Hardware, tiempos y costo

| Concepto | Valor |
|---|---|
| PC | i5-11400H, 16 GB RAM, RTX 3050 Laptop 4 GB, Windows 11 |
| Extracción de las 101 fichas | ≈ 40 min (1.76 s/página), RAM pico ≈ 6.5 GB |
| Índice (6 483 fragmentos) | 272 s |
| Respuesta del RAG | ≈ 27 s (top-k 3) / 33 s (top-k 6), de ellos ≈ 7 s de recarga de `bge-m3` en la GPU |
| Evaluación RAGAS | v1 ≈ 90 min (generación 12 min, puntuación 19 + 36 min, reintento fallido 22 min); v2 (repetición completa) 65 min (generación 12 min, puntuación 17.5 + 34.6 min) |
| AWS | `r5.large` ≈ US$ 0.126/h (tarifa de lista) usada solo durante las pruebas de la Fase 1; **detenida**. Costo estimado menor a US$ 1 del presupuesto del Learner Lab |

Detalle en `metricas/hardware.md`, `metricas/extraccion_resumen.md`, `metricas/rag_latencia.md` y `metricas/evaluacion_consumo.md`.

## 7. Limitaciones y mitigaciones

| Limitación | Mitigación / estado |
|---|---|
| Docling descarta encabezados y pies de página (donde muchas FDS ponen versión y fecha) | La versión y la fecha se buscan en el texto crudo del PDF; si no aparecen, quedan vacías |
| FDS tipo formulario: etiquetas y valores separados en el Markdown | Documentado; las preguntas de evaluación usan datos literales; el prompt avisa al generador |
| El OCR lee texto, no interpreta **pictogramas** GHS (llegó a leer íconos como ideogramas en 6 tablas) | Imágenes conservadas con página y sección; los ideogramas se eliminan al construir los fragmentos; el significado solo se usa si el texto lo dice |
| 8 fichas AkzoNobel con `producto` mal extraído («X International.») | **Corregido** el 2026-11-17 (solo cambiaron esos 8 nombres); índice reconstruido y evaluación repetida (v2) |
| Un generador de 7 B puede omitir datos, rechazar de más o citar fichas de otro producto | Prompt simplificado y fijo, citas generadas por el código, revisión manual de las citas |
| Pregunta por un producto inexistente (e12): en v1 el sistema inventaba; en v2 reconoce la falta de evidencia, pero porque el generador ve los nombres correctos en los encabezados | El filtro por producto y el aviso de «variante sin ficha» siguen sin activarse en ese caso; mejora propuesta en el análisis |
| Evaluador local de 8 B con ruido (no determinista, JSON inválido ocasional, Context Precision siempre 1.00) | Se reportan fallos como `NaN`, el número de casos válidos y la revisión manual |
| 15 fichas sin fabricante en el contenido | Se dejan vacías (no se infiere desde el nombre de archivo) |

## 8. Estructura del repositorio

```
config/       base.yaml, topk3.yaml, topk6.yaml        src/rag_fds/   extraccion, metadatos, secciones, verificacion, chunking,
infra/        scripts AWS CLI (crear, iniciar, ...)                   indice, rag, evaluacion, ... (ver cada módulo)
app/demo.py   demo Streamlit                           data/processed/  Markdown, imágenes y meta.json por ficha (data/raw/ no se sube)
eval/         preguntas, respuestas, resultados, análisis, revisión manual     verificacion/  secciones, tablas verificadas, errores de extracción
metricas/     hardware, tiempos y consumo               docs/          guía del parcial y diseño         informe/  informe y guion de la demo
```

## 9. Uso de herramientas de IA

Se usó **Claude Code** como apoyo para escribir código, scripts de infraestructura, documentación y análisis. Los autores deben verificar y poder explicar el código y las decisiones; las verificaciones contra los PDF (tablas, referencias,
citas) son manuales y están registradas como tales. Las referencias de las 12 preguntas las redactó el asistente; su evidencia está comprobada **automáticamente** contra el texto del PDF y el autor las verificó el 2026-11-17 con `eval/revision_preguntas/index.html` (12 de 12 «verificada», sin observaciones; `eval/verificacion_preguntas_autor.json`). La evaluación se había corrido antes de esa verificación (con las preguntas marcadas `true` por una declaración que se retiró y luego se confirmó); como no hubo cambios, los resultados siguen vigentes. La **extracción** se verificó con un método mixto (automático en las 1 248 tablas + asistido por IA + verificación visual del autor en 24 fichas; `verificacion/errores_extraccion.md`); los **5 casos analizados** los revisó el autor el 2026-11-17 (exactitud de cada respuesta; `eval/revision_manual_resultados_autor.md`), con una segunda lectura asistida por IA (`eval/revision_asistida_ia.md`) que discrepa en algunos bloques; el autor solo marcó la correspondencia de las citas en un caso (e09, top-k 3) y no escribió observaciones.


