# RAG con Fichas de Datos de Seguridad (FDS)

Parcial final de Procesamiento de Lenguaje Natural — Universidad Sergio Arboleda, 2026 S02.

**Autores:** Daniel Reyes, Sebastián Urrego y David Martínez.

Sistema RAG (recuperación aumentada por generación) sobre 101 Fichas de Datos de Seguridad del sector de
pinturas, con modelos open source locales (Ollama) y evaluación con RAGAS.

> Este README se completa al final del proyecto (Fase 8). Por ahora solo contiene el registro de avance.

## Avance

- [x] Fase 0 — Entorno, cuentas y plan
- [x] Fase 1 — Infraestructura en AWS (EC2 r5.large + Ollama; la inferencia se movió al PC con GPU, ver `metricas/hardware.md`)
- [x] Fase 2 — Extracción PDF → Markdown (101 fichas)
- [~] Fase 3 — Secciones y verificación de la extracción (falta la revisión manual del autor)
- [~] Fase 4 — Sistema RAG con trazabilidad (funcional; falta que el autor valide las citas de la demo, ver `docs/rag_diseno.md`)
- [~] Fase 5 — Conjunto de evaluación (borrador de 12 preguntas; falta la verificación del autor, ver `eval/revision_preguntas/index.html`)
- [~] Fase 6 — Evaluación con RAGAS (evaluador `llama3.1:8b` probado con 2 casos; la evaluación completa espera la verificación de las 12 preguntas, ver `docs/evaluacion_ragas.md`)
- [ ] Fase 7 — Revisión manual y análisis
- [ ] Fase 8 — Documentación, informe y cierre

## Uso de herramientas de IA

Se usó Claude Code como apoyo. Los autores verifican y pueden explicar el código y las decisiones.



