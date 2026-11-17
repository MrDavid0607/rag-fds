# Métricas de extracción (Fase 2)

Herramienta: Docling 2.150.1 (estructura de tablas activa, OCR RapidOCR en imágenes, imágenes a escala 2.0).

## Corpus completo (101 PDF, 1 134 páginas, 0 fallos de conversión)

| Concepto | Valor |
|---|---|
| Dónde corrió | PC del autor: i5-11400H, RTX 3050 Laptop (4 GB), 16 GB RAM, Windows 11, PyTorch 2.11.0+cu128 |
| Fichas / páginas | 101 / 1 134 |
| Tablas detectadas | 1 286 |
| Imágenes guardadas | 1 192 (más los logos duplicados, solo registrados) |
| Tiempo de conversión (suma de Docling) | ≈ 1 886 s para 1 073 páginas (≈ 1.76 s/página) más 143 s de la muestra de 5 fichas |
| Reloj total aproximado | ≈ 40 min en tres ejecuciones (muestra + dos tandas; la primera tanda se interrumpió tras la ficha 41 y se reanudó sin repetir las ya terminadas) |
| RAM pico del proceso (tanda 2) | ≈ 6.5 GB |
| Tamaño de `data/processed/` | ≈ 14 MB |

La segunda tanda (59 fichas, 743 páginas) tardó 1 217 s ≈ 1.64 s/página (`extraccion_completa_pc_gpu_parte2.json`).

## Comparación EC2 (CPU) vs PC (GPU) sobre la misma muestra de 5 fichas (61 páginas)

| Dónde | Tiempo | s/página |
|---|---|---|
| EC2 r5.large (2 vCPU) | 1 048 s | 17.2 |
| PC con GPU | 143 s (incluye ≈ 85 s de carga de modelos) | 2.35 |

Con la velocidad de la EC2 el corpus completo habría tardado ≈ 5.4 h; en el PC, ≈ 40 min. Por eso la extracción
final se hizo en el PC (ver `hardware.md`). Consumo en la EC2: ≈ 0.14 US$/h; no se usó para la corrida final.
