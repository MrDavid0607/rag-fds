"""Imprime una tabla por pregunta con las puntuaciones de topk3 y topk6 (para el análisis de la Fase 7)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def cargar(k):
    return {r["id"]: r for r in json.loads(Path(f"eval/resultados_{k}.json").read_text(encoding="utf-8"))["resultados"]}


def f(v):
    return "NaN" if v is None else f"{v:.2f}"


a, b = cargar("topk3"), cargar("topk6")
print(f"{'id':4} {'tipo':24} | topk3: F    CP   CR  | topk6: F    CP   CR  | citas_inval 3/6 | insuf 3/6")
for i in sorted(a):
    x, y = a[i], b[i]
    print(f"{i:4} {x['tipo'][:24]:24} |  {f(x['faithfulness']):>4} {f(x['context_precision']):>4} {f(x['context_recall']):>4} |  {f(y['faithfulness']):>4} {f(y['context_precision']):>4} {f(y['context_recall']):>4} |"
          f"  {len(x['citas_invalidas'])}/{len(y['citas_invalidas'])}  |  {int(x['evidencia_insuficiente'])}/{int(y['evidencia_insuficiente'])}")
errs = [(k, r["id"], m, r[f"error_{m}"]) for k, d in (("topk3", a), ("topk6", b)) for r in d.values() for m in ("faithfulness", "context_precision", "context_recall") if r.get(f"error_{m}")]
print("\nErrores del evaluador:", errs if errs else "ninguno")
for k, d in (("topk3", a), ("topk6", b)):
    print(k, "t_generación media:", round(sum(r["t_generacion_s"] for r in d.values()) / len(d), 1), "s | tokens prompt medio:", round(sum(r["tokens_prompt"] for r in d.values()) / len(d)))
