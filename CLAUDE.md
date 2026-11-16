# CLAUDE.md — Parcial final de NLP: RAG con Fichas de Datos de Seguridad (FDS)

Este archivo es la guía de trabajo para Claude Code. Léelo completo al empezar cada sesión.
Responde y escribe todo (código comentado, README, informe) **en español**.

## 0. Contexto

- Curso: Procesamiento de Lenguaje Natural, Universidad Sergio Arboleda, 2026 S02.
- Trabajo **individual**. El autor debe poder explicar y verificar cada decisión en la demostración,
  así que explica lo que haces de forma clara y deja todo documentado.
- La guía oficial está en `docs/guia/RAG_FDS.pdf`. Ante cualquier duda, **la guía manda** sobre este archivo.
- Corpus: `data/raw/FDS EVALUADAS/` — **101 PDFs, 1 134 páginas**, carpetas por año (`FDS 2018` … `FDS 2025`).
  Ninguno es escaneado (todos tienen capa de texto). Fabricantes: Pintuco, Corona, PPG, Pintuland, INVESA,
  Sika, AkzoNobel/International, Bler y otros. En varios archivos el fabricante **no** está en el nombre:
  hay que sacarlo del contenido. Hay productos repetidos en distintas versiones
  (p. ej. "Pintura Primera Mano & Acabado - Corona" en 2019 y en 2021). Los nombres de archivo traen
  escapes como `#U00ed` (= í): decodifícalos para mostrar, pero conserva el nombre original como procedencia.

## 1. Reglas que no se rompen

1. **Nada de APIs pagas** (ni OpenAI, ni Anthropic, ni Cohere, ni para evaluar). Todo open source y local
   o en la EC2 propia. Modelos de lenguaje y embeddings: **Ollama**.
2. **Nunca inventar contenido de las FDS.** No completar secciones por inferencia. Si algo no se encuentra,
   se registra como ausente o como fallo de extracción, nunca se rellena.
3. **Credenciales fuera del repositorio**, siempre: claves de AWS, tokens, `.pem`, `.env`. Revisa
   `git diff --cached` antes de cada commit buscando `AKIA`, `ASIA`, `aws_secret`, `aws_session_token`,
   `ghp_`, `BEGIN RSA` y `BEGIN OPENSSH`.
4. **Las respuestas de referencia nunca entran al índice ni al prompt del generador.**
5. **Las dos configuraciones de evaluación solo difieren en top-k.** Corpus, chunking, embeddings,
   generador, prompt y evaluador son idénticos y quedan fijados en un archivo de configuración.
6. **Fallos de RAGAS se registran como fallos** (`NaN` + mensaje de error), nunca como 0.
7. **Las preguntas de desarrollo son distintas a las 12 de evaluación.**
8. **No marques como "verificado por humano" nada que no haya revisado el autor.** Puedes hacer
   pre-chequeos automáticos, pero la columna de verificación manual la llena él.
9. **Pausa al final de cada fase**: resume qué hiciste, qué quedó pendiente y qué debe revisar el autor,
   y espera su aprobación antes de seguir.
10. **Apaga la EC2** (`aws ec2 stop-instances`) cuando termine un trabajo largo o el autor diga que deja
    de trabajar. El presupuesto del Learner Lab es limitado.
11. Dependencias **con versión fija** en `requirements.txt` (genera con `pip freeze` filtrado o `pip-compile`).

## 2. Arquitectura

```
PC del autor (Claude Code)                       AWS Learner Lab · us-east-1
───────────────────────────                      ─────────────────────────────────────
repo git local  ── rsync por SSH ───────────────► EC2 (Ubuntu 24.04)
  │                                                ├─ Docling: PDF → Markdown + imágenes
  │                                                ├─ Ollama (solo 127.0.0.1:11434)
  │                                                │    embeddings bge-m3 · generador · evaluador
  │                                                ├─ Chroma (índice persistente)
  │                                                ├─ RAGAS
  │  ◄── rsync de resultados ──────────────────────┘ └─ App de demo (Streamlit, 127.0.0.1:8501)
  │
  └─ git push ──► GitHub (cuenta MrDavid0607)     Acceso a Ollama/app: túnel SSH, nunca puertos abiertos
```

- **No se usa SageMaker**: la guía no lo exige y una EC2 es más simple de operar por CLI.
- **S3 es opcional**: solo como respaldo de `data/processed/` y del índice al cerrar fases grandes.
- El código vive en el repo local; la EC2 recibe copias por `rsync`. **En la EC2 no hay credenciales de GitHub.**
- Esta decisión (simplicidad operativa vs. costo vs. desempeño) debe justificarse en el README, porque es
  parte del criterio de "Arquitectura, reproducibilidad y eficiencia" (15 %).

## 3. Estructura del repositorio

```
rag-fds/
├── CLAUDE.md
├── README.md
├── requirements.txt              # versiones fijadas
├── config/
│   ├── base.yaml                 # chunking, embeddings, generador, prompt, evaluador (constantes)
│   ├── topk3.yaml                # hereda base, top_k: 3
│   └── topk6.yaml                # hereda base, top_k: 6
├── infra/                        # scripts AWS CLI (crear, iniciar, detener, ssh, túnel, sync)
├── src/rag_fds/
│   ├── extraccion.py             # Docling → Markdown + imágenes + procedencia de página
│   ├── metadatos.py              # fabricante, producto, versión/fecha, hash
│   ├── secciones.py              # detección de las 16 secciones y su estado
│   ├── verificacion.py           # pre-chequeo automático y página de revisión manual
│   ├── chunking.py
│   ├── indice.py                 # embeddings + Chroma
│   ├── rag.py                    # recuperación + generación con citas
│   └── evaluacion.py             # RAGAS
├── app/demo.py                   # interfaz de demostración
├── data/
│   ├── raw/                      # PDFs (ver decisión en Fase 0)
│   └── processed/<doc_id>/       # documento.md, imagenes/, meta.json
├── verificacion/
│   ├── verificacion_extraccion.csv
│   ├── errores_extraccion.md
│   └── secciones.csv
├── eval/
│   ├── preguntas.json            # las 12 preguntas + referencias + evidencia
│   ├── preguntas_desarrollo.json
│   ├── resultados_topk3.{csv,json}
│   ├── resultados_topk6.{csv,json}
│   ├── resumen.csv
│   └── revision_manual.md
├── docs/guia/RAG_FDS.pdf
├── metricas/                     # hardware, tiempos, RAM, tokens/s, costo
└── informe/informe.md (+ PDF de máximo 2 páginas)
```

## 4. Fases

### Fase 0 — Entorno, cuentas y plan

1. **GitHub**: verifica que la cuenta activa sea **MrDavid0607** con `gh auth status` y `git config user.name`
   / `user.email`. Si no lo es, detente y pídele al autor que inicie sesión (`gh auth login`); no cambies de
   cuenta por tu cuenta.
2. Crea el repositorio `rag-fds` en MrDavid0607 como **privado** por ahora (`gh repo create`). Antes de la
   entrega se hará público o se dará acceso al docente: pregunta al autor cuál prefiere.
3. **Pregunta al autor** si los PDFs originales van al repositorio. Por defecto: `data/raw/` en `.gitignore`
   y el README explica dónde ponerlos; los Markdown e imágenes extraídas sí se suben.
4. `.gitignore` con: `.env`, `*.pem`, `.aws/`, `data/raw/`, `__pycache__/`, `.venv/`, índices pesados si
   superan lo razonable.
5. **AWS CLI**:
   - Verifica que esté instalada (`aws --version`); si no, guía la instalación para el sistema del autor.
   - Las credenciales del Learner Lab son **temporales** y vencen con cada sesión. Pídele al autor que en
     la página del Learner Lab haga *Start Lab* → *AWS Details* → *AWS CLI: Show* y pegue el bloque en
     `~/.aws/credentials` bajo el perfil **`[academy]`** (no en `default`). Región: `us-east-1`.
   - Usa siempre `AWS_PROFILE=academy`. Comprueba con `aws sts get-caller-identity`.
   - Si una llamada falla por `ExpiredToken` o similar, **no reintentes en bucle**: pide credenciales nuevas.
6. Pide al autor su nombre completo tal como debe aparecer en el README y el informe.
7. Presenta un plan corto de las fases y espera aprobación.

### Fase 1 — Infraestructura en AWS (todo por CLI, scripts en `infra/`)

1. Llave SSH: créala con `aws ec2 create-key-pair` y guárdala en `~/.ssh/rag-fds.pem` (permisos 600),
   **fuera del repo**. Si el Learner Lab bloquea la creación, usa la llave `vockey` del lab
   (`labsuser.pem`, descargable en *AWS Details*).
2. Security Group `rag-fds-sg`: solo puerto **22** desde la IP pública actual del autor
   (`curl -s https://checkip.amazonaws.com`). Nada más abierto. Script para actualizar la IP si cambia.
3. AMI de Ubuntu 24.04 vía parámetro SSM
   `/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id`
   (si no hay permiso, `describe-images` con owner Canonical `099720109477`).
4. Instancia: intenta **`m5.2xlarge`** (8 vCPU, 32 GB) con **80 GB gp3**, perfil de instancia
   `LabInstanceProfile`, tag `Project=rag-fds`. Si el Learner Lab no permite ese tipo, prueba `t3.2xlarge`
   y luego `m5.xlarge`, y documenta cuál quedó y por qué. No intentes instancias GPU sin consultar al autor.
5. Scripts en `infra/`: `crear.sh`, `iniciar.sh`, `detener.sh`, `estado.sh`, `ssh.sh`,
   `tunel.sh` (reenvía 11434 y 8501 a localhost), `sync_subir.sh`, `sync_bajar.sh`.
   La IP pública cambia en cada arranque: los scripts la consultan por tag, no la escriben fija.
   (Una Elastic IP es opcional; si se usa, que quede documentado.)
6. En la EC2: Python 3.11+ con venv, `rsync`, y **Ollama** instalado con su script oficial, escuchando
   solo en `127.0.0.1`. Descarga los modelos y registra **nombre, etiqueta y digest**
   (`ollama list`, `ollama show`):
   - Embeddings: `bge-m3` (multilingüe, bueno en español).
   - Generador: `qwen2.5:7b-instruct` (buen español y salida estructurada).
   - Evaluador RAGAS: un modelo **distinto** del generador para reducir el sesgo de autoevaluación,
     por ejemplo `llama3.1:8b` o `gemma2:9b`. Se valida en la Fase 6 con dos casos.
   Si la RAM o la velocidad no alcanzan, propón alternativas más pequeñas y documenta el cambio.
7. Comprueba: Ollama responde a una instrucción, `bge-m3` devuelve un vector y el túnel funciona desde el PC.
8. Registra en `metricas/hardware.md`: tipo de instancia, vCPU, RAM, disco, región, versión de Ollama
   y de los modelos, costo por hora de la instancia.

**Checkpoint**: el autor confirma que puede entrar por `infra/ssh.sh` y ver Ollama por el túnel.

### Fase 2 — Extracción PDF → Markdown (criterio de 30 %, el más pesado)

1. Herramienta: **Docling** (versión fijada), con estructura de tablas activada, exportación de imágenes
   y procedencia de página por elemento. OCR (RapidOCR o EasyOCR) **solo** para texto dentro de imágenes,
   ya que los PDFs tienen capa de texto.
2. **Primero 5 fichas** de fabricantes y años distintos. Muéstralas al autor junto a su PDF. Solo con su
   aprobación procesas las 101.
3. Por ficha, en `data/processed/<doc_id>/`:
   - `documento.md` conservando títulos, tablas, listas, notas, unidades y referencias. Marca de página
     visible (por ejemplo `<!-- pagina: 3 -->`) para no perder la trazabilidad.
   - `imagenes/`: imágenes con información técnica (pictogramas, tablas en imagen, logos de transporte),
     enlazadas desde el Markdown con **rutas relativas**, cada una con su página y sección registradas.
     Una imagen se asocia a una tabla **solo si hay evidencia** de esa relación en el documento.
   - `meta.json`: `doc_id`, archivo original, carpeta/año (procedencia), `sha256`, fabricante, producto,
     código de producto si existe, **versión y fecha de revisión** tal como aparecen en el PDF, número de
     páginas, herramienta y versión de extracción. Campo vacío + nota si un dato no aparece: no se infiere.
4. `doc_id` estable y legible, por ejemplo `fds057-pintuco-acrolatex-50-3508`.
5. Registra tiempo total, tiempo por página y RAM pico en `metricas/`.
6. Documenta en `verificacion/errores_extraccion.md` las limitaciones del OCR con pictogramas: el OCR lee
   texto, no interpreta el significado de un pictograma GHS.

### Fase 3 — Secciones y verificación de la extracción

1. **Las 16 secciones de una FDS**: 1 Identificación del producto y de la empresa · 2 Identificación de
   peligros · 3 Composición / información sobre los componentes · 4 Primeros auxilios · 5 Medidas de lucha
   contra incendios · 6 Medidas en caso de vertido accidental · 7 Manipulación y almacenamiento ·
   8 Controles de exposición / protección personal · 9 Propiedades físicas y químicas · 10 Estabilidad y
   reactividad · 11 Información toxicológica · 12 Información ecológica · 13 Consideraciones relativas a
   la eliminación · 14 Información relativa al transporte · 15 Información reglamentaria · 16 Otra información.
   Los títulos varían entre fabricantes: usa patrones flexibles (número + palabras clave, mayúsculas,
   sinónimos) y revisa casos raros a mano.
2. Estado por sección en `verificacion/secciones.csv` (`doc_id`, sección, estado, página, evidencia):
   - `presente`: el encabezado está en el Markdown.
   - `fallo_extraccion`: el encabezado aparece en el texto crudo del PDF (`pypdfium2`/`pdfplumber`) pero
     no en el Markdown.
   - `ausente_en_original`: no está en el Markdown ni en el texto crudo. Márcala para revisión del autor.
3. **Verificación de tablas** (la guía exige al menos una tabla o bloque con datos por ficha):
   - Elige en cada ficha una tabla con datos (sección 3, 8 o 9 suelen tenerlas).
   - Pre-chequeo automático: compara números y unidades de la tabla en el Markdown contra el texto crudo
     de esa página y anota diferencias.
   - Genera `verificacion/revision.html`: por ficha, la imagen de la página del PDF al lado del bloque en
     Markdown, para que el autor revise rápido.
   - `verificacion/verificacion_extraccion.csv`: `doc_id`, página, sección, elemento revisado,
     resultado_auto, diferencias_auto, **verificado_por_autor** (vacío hasta que él lo llene),
     errores_encontrados, observaciones.
4. Resume en `errores_extraccion.md` los tipos de error encontrados y cómo se mitigaron.

**Checkpoint**: el autor revisa `revision.html` y llena su columna. Ofrécele dividirlo en tandas de 20.

### Fase 4 — Sistema RAG con trazabilidad (25 %)

1. **Chunking** guiado por estructura: primero por sección de la FDS, luego por tamaño si la sección es
   larga. Punto de partida: ~800 caracteres con ~150 de solapamiento, **sin partir tablas** (una tabla
   larga se divide por filas repitiendo el encabezado). Cada chunk lleva en su texto un encabezado corto
   con fabricante, producto, versión y sección, y en sus metadatos: `doc_id`, fabricante, producto,
   versión/fecha, archivo, página(s), número y nombre de sección, rutas de imágenes asociadas.
2. **Embeddings** con `bge-m3` vía Ollama; índice persistente en **Chroma**. Documenta tamaño de chunk,
   solapamiento, número de chunks, modelo de embeddings y top-k.
3. **Filtros por metadatos**: si la consulta nombra un fabricante, producto o año/versión, filtra antes
   de buscar. Para comparaciones entre productos, recupera por producto para no dejar uno sin contexto.
4. **Generación** con el prompt fijo de `config/base.yaml`:
   - Responder **solo** con los fragmentos recuperados.
   - Cada afirmación con cita `[n]`, y al final la lista de fuentes:
     fabricante · producto · versión · documento · página · sección.
   - Si la evidencia no alcanza: decirlo explícitamente ("No hay evidencia suficiente en las FDS
     disponibles para…") en lugar de completar.
   - Temperatura baja (0–0.1) y semilla fija para reproducibilidad.
5. CLI (`python -m rag_fds.rag "pregunta" --config config/topk6.yaml`) y **app de demo** en Streamlit
   (accesible solo por el túnel) que muestre la respuesta, las citas, los fragmentos recuperados en orden
   y las imágenes asociadas cuando existan.
6. Mide latencia de recuperación y de generación, y tokens por segundo.
7. Prueba con `eval/preguntas_desarrollo.json` (preguntas **distintas** a las de evaluación).

**Checkpoint**: demo funcional con 3–4 preguntas de desarrollo; el autor valida citas contra el PDF.

### Fase 5 — Conjunto de evaluación

1. Propón **12 preguntas** en `eval/preguntas.json`:
   - 6 de consulta directa.
   - 4 que integren dos secciones o comparen productos (incluye al menos una que compare **dos versiones
     del mismo producto**).
   - 2 **sin respuesta** sustentada en el corpus (plausibles, sobre productos o datos que no están).
   - Cubrir al menos **4 secciones distintas** e identificar los productos consultados.
2. Para las 10 respondibles, redacta un borrador de referencia **con la evidencia exacta**: fragmento,
   documento, página y sección. El autor **verifica cada una contra el PDF** y marca `verificada: true`.
   Sin esa marca no se evalúa.
3. Las referencias se guardan solo en `eval/`; el índice y el generador nunca las leen.

**Checkpoint**: el autor aprueba las 12 preguntas y sus referencias.

### Fase 6 — Evaluación con RAGAS (20 %)

1. Fija la versión de RAGAS y **revisa la documentación de esa versión** para usar un LLM y embeddings
   locales (envoltorios de LangChain sobre Ollama). Registra versiones de `ragas`, `langchain-*`, modelo
   evaluador, temperatura, `num_ctx`, timeouts y paralelismo.
2. Métricas: **Faithfulness**, **Context Precision con referencia** y **Context Recall**.
3. En CPU usa poco paralelismo (1–2 workers) y timeouts largos. Si el evaluador devuelve JSON inválido,
   ajusta la configuración, pero **nunca** conviertas el fallo en 0.
4. **Primero 2 casos** con el evaluador, revisa que las puntuaciones tengan sentido y muéstraselo al autor.
5. Corre `topk3` y `topk6` sobre las 10 respondibles con el mismo evaluador. Guarda por pregunta y
   configuración: `user_input`, `retrieved_contexts` (en orden), `response`, `reference`, `fuentes`,
   puntuaciones y errores. Formatos CSV y JSON.
6. `eval/resumen.csv`: promedio por métrica y configuración, y **número de casos válidos** por métrica.
7. Corre también las 2 preguntas sin respuesta en ambas configuraciones y guarda sus respuestas
   (no se puntúan con RAGAS; se revisan aparte).
8. Registra tiempo total de evaluación y consumo de la instancia.

### Fase 7 — Revisión manual y análisis

1. `eval/revision_manual.md` con plantilla para:
   - Las 2 preguntas sin respuesta: ¿reconoce la falta de evidencia o inventa?
   - 3 casos respondibles, incluyendo los de **menor puntuación**: exactitud de la respuesta y
     correspondencia de cada cita con el PDF (página y sección correctas).
2. Prepara la información, pero **las conclusiones de exactitud las confirma el autor** mirando los PDFs.
3. Explica los errores observados (recuperación, chunking, generación, o el evaluador mismo) y justifica
   la configuración elegida. El conjunto de 12 preguntas permite una comparación didáctica, no prueba
   que una configuración sea mejor en general: dilo así.

### Fase 8 — Documentación, informe y cierre

1. **README**: qué es, arquitectura (con el diagrama), cómo reproducirlo de cero (AWS por CLI, EC2,
   modelos, extracción, índice, RAG, evaluación, demo), modelos y versiones, estrategia de chunking,
   decisiones y su justificación, hardware, tiempos y costo, limitaciones y mitigaciones, uso de
   herramientas de IA (Claude Code) declarado.
2. **Informe de máximo 2 páginas** (`informe/informe.md` → PDF): comparación top-k 3 vs 6, los tres casos
   analizados, limitaciones y conclusión. Verifica que quede en 2 páginas.
3. **Guion de demostración** (`informe/guion_demo.md`): cómo arrancar todo, 4–5 preguntas que muestren
   citas, un caso sin evidencia y una comparación de versiones, y las preguntas que probablemente haga
   el docente con respuesta corta.
4. Barrido final de credenciales en todo el historial de git (`git log -p | grep -E "AKIA|ASIA|ghp_|PRIVATE KEY"`).
5. Pregunta al autor si se hace público el repo o se agrega al docente como colaborador.
6. Respaldo opcional a S3 y **detener la EC2**.

## 5. Checklist final de la guía

- [ ] Las 101 FDS procesadas a Markdown, con procedencia y versión registradas.
- [ ] Títulos, tablas, listas, notas, unidades y referencias preservados.
- [ ] Al menos una tabla o bloque verificado contra cada PDF, con errores registrados.
- [ ] Secciones presentes identificadas; ausentes distinguidas de fallos de extracción; nada inferido.
- [ ] RAG funcional con modelos locales o infraestructura propia.
- [ ] Chunking, tamaño, solapamiento, embeddings y top-k documentados.
- [ ] Consultas sobre todas las FDS, diferenciando fabricante, producto y versión.
- [ ] Cada afirmación citada con fabricante, producto, documento, página y sección.
- [ ] El sistema avisa cuando la evidencia es insuficiente; limitaciones y mitigaciones documentadas.
- [ ] Imágenes técnicas conservadas y enlazadas con rutas relativas; página y sección registradas.
- [ ] OCR aplicado donde hace falta y limitaciones con pictogramas documentadas.
- [ ] Solo herramientas open source; sin APIs pagas, tampoco para evaluar.
- [ ] Hardware y consumo documentados; arquitectura justificada (desempeño, costo, complejidad).
- [ ] 12 preguntas: 6 directas, 4 integradoras/comparativas, 2 sin respuesta; ≥ 4 secciones.
- [ ] Referencias verificadas contra los PDF con evidencia; fuera del índice y del prompt.
- [ ] top-k 3 vs top-k 6, todo lo demás constante; preguntas de desarrollo distintas.
- [ ] Faithfulness, Context Precision y Context Recall en las 10 respondibles, ambas configuraciones.
- [ ] Resultados por pregunta con todos los campos pedidos; promedios y número de casos válidos.
- [ ] Fallos de evaluación registrados como fallos.
- [ ] Evaluador local probado primero con 2 casos; versiones y parámetros registrados; el mismo en ambas.
- [ ] Revisión manual de las 2 sin respuesta y de 3 respondibles (incluidas las de menor puntuación).
- [ ] Repositorio con dependencias fijadas y README completo.
- [ ] Informe de máximo 2 páginas.
- [ ] Demo funcional y guion listo.
- [ ] Sin credenciales en el repositorio.

## 6. Al comenzar cada sesión de trabajo

1. Lee este archivo y revisa en qué fase va el proyecto (`git log`, `README.md` sección "Avance").
2. `AWS_PROFILE=academy aws sts get-caller-identity`. Si falla, pide credenciales nuevas del Learner Lab.
3. `infra/estado.sh`; si la EC2 está detenida y hace falta, `infra/iniciar.sh`.
4. Actualiza la IP del Security Group si la del autor cambió.
5. Al terminar: commit y push desde el PC, y detén la EC2 si no queda nada corriendo.
