"""Muestra los pasos internos de Faithfulness (afirmaciones y veredictos) para un caso, para entender una puntuación baja.

Uso:
  python -m rag_fds.diagnostico_evaluador p2                      # caso piloto (eval/piloto_evaluador.json)
  python -m rag_fds.diagnostico_evaluador topk6 e04               # caso de evaluación (eval/resultados_topk6.json)
Añade --con-citas para NO quitar las marcas [n] de la respuesta (así se vio el artefacto de las citas).
Con --salida <archivo.json> guarda afirmaciones y veredictos.
"""
from __future__ import annotations

import asyncio
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from rag_fds.config import cargar
from rag_fds.evaluacion import crear_metricas, quitar_citas


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) == 1:
        datos = {c["id"]: c for c in json.load(open("eval/piloto_evaluador.json", encoding="utf-8"))["casos"]}[args[0]]
    else:
        datos = {r["id"]: r for r in json.load(open(f"eval/resultados_{args[0]}.json", encoding="utf-8"))["resultados"]}[args[1]]
    cfg = cargar("config/topk6.yaml")
    fa = crear_metricas(cfg)["faithfulness"]
    sin_citas = "--con-citas" not in sys.argv
    fila = {"user_input": datos["user_input"], "retrieved_contexts": datos["retrieved_contexts"],
            "response": quitar_citas(datos["response"]) if sin_citas else datos["response"], "reference": datos["reference"]}

    async def pasos():
        salida = await fa._create_statements(fila, None)
        afirmaciones = list(salida.statements)
        return afirmaciones, await fa._create_verdicts(fila, afirmaciones, None)

    afirmaciones, veredictos = asyncio.run(pasos())
    print("RESPUESTA EVALUADA:", fila["response"])
    print("\nVEREDICTOS (1 = respaldada por los contextos, 0 = no). RAGAS genera las afirmaciones en inglés:")
    registro = []
    for v in veredictos.statements:
        print(f" - [{v.verdict}] {v.statement}\n       razón: {v.reason[:400]}")
        registro.append({"verdict": v.verdict, "statement": v.statement, "reason": v.reason})
    if "--salida" in sys.argv:
        Path(sys.argv[sys.argv.index("--salida") + 1]).write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
