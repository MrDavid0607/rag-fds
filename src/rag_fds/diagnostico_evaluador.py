"""Muestra los pasos internos de Faithfulness (afirmaciones y veredictos) para un caso del piloto, para comprobar
que las puntuaciones del evaluador local tienen sentido.

Uso: python -m rag_fds.diagnostico_evaluador p2
"""
from __future__ import annotations

import asyncio
import inspect
import json
import sys
import warnings

warnings.filterwarnings("ignore")

from rag_fds.config import cargar
from rag_fds.evaluacion import crear_metricas


def main() -> None:
    caso = sys.argv[1] if len(sys.argv) > 1 else "p2"
    datos = {c["id"]: c for c in json.load(open("eval/piloto_evaluador.json", encoding="utf-8"))["casos"]}[caso]
    cfg = cargar("config/topk6.yaml")
    fa = crear_metricas(cfg)["faithfulness"]
    from rag_fds.evaluacion import quitar_citas

    sin_citas = "--con-citas" not in sys.argv
    fila = {"user_input": datos["user_input"], "retrieved_contexts": datos["retrieved_contexts"],
            "response": quitar_citas(datos["response"]) if sin_citas else datos["response"], "reference": datos["reference"]}

    async def pasos():
        salida = await fa._create_statements(fila, None)
        afirmaciones = list(salida.statements)
        veredictos = await fa._create_verdicts(fila, afirmaciones, None)
        return afirmaciones, veredictos

    afirmaciones, veredictos = asyncio.run(pasos())
    print("RESPUESTA:", datos["response"])
    print("\nAFIRMACIONES extraídas por el evaluador (RAGAS las genera en inglés):")
    for s in afirmaciones:
        print(" -", s)
    print("\nVEREDICTOS (1 = respaldada por los contextos, 0 = no):")
    for v in veredictos.statements:
        print(f" - [{v.verdict}] {v.statement}\n       razón: {v.reason[:300]}")


if __name__ == "__main__":
    main()
