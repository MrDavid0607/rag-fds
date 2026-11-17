"""Corre las preguntas de DESARROLLO (eval/preguntas_desarrollo.json) y guarda respuestas, citas, fragmentos y tiempos.

Sirve para revisar a mano recuperación, citas y rechazo por falta de evidencia. NO son las preguntas de evaluación.
Uso: python -m rag_fds.desarrollo --config config/topk6.yaml --salida eval/desarrollo_topk6.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_fds.config import cargar
from rag_fds.indice import abrir_coleccion
from rag_fds.rag import cargar_catalogo, formato_texto, responder


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/topk6.yaml")
    ap.add_argument("--preguntas", type=Path, default=Path("eval/preguntas_desarrollo.json"))
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--ids", nargs="*", help="solo estas preguntas (p. ej. dev02 dev03)")
    args = ap.parse_args()
    cfg = cargar(args.config)
    col, cat = abrir_coleccion(cfg), cargar_catalogo(cfg["corpus"]["procesados"])
    preguntas = json.loads(args.preguntas.read_text(encoding="utf-8"))["preguntas"]
    if args.ids:
        preguntas = [q for q in preguntas if q["id"] in set(args.ids)]
    resultados = []
    for q in preguntas:
        r = responder(q["pregunta"], cfg, col, cat)
        r["id"], r["tipo"] = q["id"], q["tipo"]
        resultados.append(r)
        print(f"\n===== {q['id']} ({q['tipo']}) =====")
        print(formato_texto(r), flush=True)
    args.salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    ts = [r["t_generacion_s"] for r in resultados]
    tk = [r["tokens_por_s"] for r in resultados if r["tokens_por_s"]]
    print(f"\nResumen: generación media {sum(ts) / len(ts):.1f} s · {sum(tk) / len(tk):.1f} tokens/s · "
          f"recuperación media {sum(r['t_recuperacion_s'] for r in resultados) / len(resultados):.2f} s")


if __name__ == "__main__":
    main()
