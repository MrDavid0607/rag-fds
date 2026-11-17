"""Compara la evaluación v1 (antes de corregir los metadatos de producto de 8 fichas AkzoNobel) con la v2 (actual).

Uso: python -m rag_fds.comparar_versiones
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
V1 = Path("eval/v1_antes_correccion_metadatos")
M = ("faithfulness", "context_precision", "context_recall")


def cargar(base: Path, k: str) -> dict:
    return {r["id"]: r for r in json.loads((base / f"resultados_{k}.json").read_text(encoding="utf-8"))["resultados"]}


def f(v):
    return "NaN" if v is None else f"{v:.2f}"


for k in ("topk3", "topk6"):
    a, b = cargar(V1, k), cargar(Path("eval"), k)
    print(f"\n== {k}:  v1 -> v2 (F | CP | CR)")
    for i in sorted(a):
        x, y = a[i], b[i]
        cambio = "  <- respuesta distinta" if x["response"].strip() != y["response"].strip() else ""
        print(f"{i}: {f(x['faithfulness'])}->{f(y['faithfulness'])} | {f(x['context_precision'])}->{f(y['context_precision'])} | {f(x['context_recall'])}->{f(y['context_recall'])}{cambio}")
    for m in M:
        va = [r[m] for r in a.values() if r.get(m) is not None]
        vb = [r[m] for r in b.values() if r.get(m) is not None]
        print(f"   {m}: v1 {sum(va)/len(va):.3f} ({len(va)} válidos) -> v2 {sum(vb)/len(vb):.3f} ({len(vb)} válidos)")
    errs = [(r["id"], m, r[f"error_{m}"][:60]) for r in b.values() for m in M if r.get(f"error_{m}")]
    print("   errores v2:", errs or "ninguno")

for k in ("topk3", "topk6"):
    a = {r["id"]: r for r in json.loads((V1 / f"respuestas_{k}.json").read_text(encoding="utf-8"))}
    b = {r["id"]: r for r in json.loads(Path(f"eval/respuestas_{k}.json").read_text(encoding="utf-8"))}
    for i in ("e11", "e12"):
        print(f"\n[{k}] {i} v1 insuficiente={a[i]['evidencia_insuficiente']} -> v2 insuficiente={b[i]['evidencia_insuficiente']}")
        print("   v2:", b[i]["response"][:220].replace("\n", " "))
