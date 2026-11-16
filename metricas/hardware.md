# Hardware y consumo — Fase 1

Fecha de medición: 2026-11-16 (AWS Academy Learner Lab, región us-east-1).

## Instancia

| Campo | Valor |
|---|---|
| Tipo | **r5.large** |
| vCPU | 2 (Intel Xeon Platinum 8259CL @ 2.50 GHz) |
| RAM | 16 GB (15 GiB visibles) |
| Disco | 80 GB gp3 (raíz `/dev/sda1`) |
| SO | Ubuntu 24.04.5 LTS, Python 3.12.3 |
| Perfil IAM | `LabInstanceProfile` |
| Tag | `Project=rag-fds` |
| Costo | ~US$ 0.126/h (tarifa on-demand de lista us-east-1, sin descuentos del lab) + gp3 80 GB ≈ US$ 0.011/h |
| Acceso | Solo SSH (puerto 22) desde la IP del autor; Ollama en 127.0.0.1 y túnel SSH |

### Por qué no es `m5.2xlarge`

El plan pedía `m5.2xlarge` (8 vCPU, 32 GB). La política IAM del Learner Lab (`Pvoclabs2`) devuelve
*explicit deny* para `ec2:RunInstances` en `m5.2xlarge`, `t3.2xlarge`, `m5.xlarge`, `t3.xlarge`,
`m6i.xlarge`, `c5.xlarge`, `c5.2xlarge`, `r5.xlarge` y `g4dn.xlarge`. Con `--dry-run` solo pasaron los
tamaños **large** (`t3.large`, `m5.large`, `m6i.large`, `r5.large`, `r6i.large`). Se eligió `r5.large`
por tener el doble de RAM (16 GB) que `m5.large`/`t3.large`. Consecuencia: solo 2 vCPU, por lo que la
inferencia en CPU es lenta (ver abajo).

## Software y modelos (Ollama 0.40.16, escuchando solo en 127.0.0.1:11434)

| Rol | Modelo | Parámetros / cuantización | Digest (sha256) |
|---|---|---|---|
| Embeddings | `bge-m3:latest` | 567 M, F16, vectores de 1024 dim | `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab` |
| Generador (candidato) | `qwen2.5:7b-instruct` | 7.6 B, Q4_K_M | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` |
| Evaluador (candidato) | `llama3.1:8b` | 8.0 B, Q4_K_M | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` |

Ollama se instala con su script oficial; `OLLAMA_MAX_LOADED_MODELS=1` y `OLLAMA_NUM_PARALLEL=1`.

## Prueba de humo (2026-11-16)

- Ollama responde a una instrucción en español: sí (ambos modelos).
- `bge-m3` devuelve un vector de 1024 dimensiones: sí (también desde el PC por el túnel).
- Túnel SSH `infra/tunel.sh`: Ollama accesible en `localhost:11434` del PC.

## Velocidad medida en CPU (2 vCPU)

Prompt corto, `temperature=0`, `seed=42`, 60 tokens máx.:

| Modelo | Generación | Carga inicial |
|---|---|---|
| `qwen2.5:7b-instruct` | ~1.7 tokens/s | ~9 s |
| `llama3.1:8b` | ~1.6 tokens/s | ~10 s |
| `bge-m3` (1 frase) | ~2.7 s | — |

Con estas velocidades, un RAG con ~3 000 tokens de contexto y la evaluación RAGAS (muchas llamadas
largas al LLM evaluador) serían muy lentos. Se evalúan alternativas en la revisión de la Fase 1
(modelos más pequeños, o Ollama en el PC del autor con GPU); la decisión se registrará aquí.

## Historial de decisiones

- 2026-11-16: instancia `r5.large` por restricciones del Learner Lab (ver arriba).
