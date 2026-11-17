"""Evaluación con RAGAS (Fase 6): Faithfulness, Context Precision (con referencia) y Context Recall.

Todo local: el LLM evaluador es un modelo de Ollama envuelto con LangChain (ChatOllama -> LangchainLLMWrapper). Estas tres
métricas solo usan el LLM (no usan embeddings). Ninguna API de pago.

Etapas (cada una se puede repetir; guardan resultados parciales):
  piloto   prueba el evaluador con 2 casos de eval/pilotos_evaluador.json (preguntas de DESARROLLO) y muestra los pasos.
  generar  para cada pregunta VERIFICADA corre el RAG con la configuración dada y guarda respuesta, contextos y fuentes.
           Las 2 sin respuesta se guardan aparte (no se puntúan con RAGAS).
  puntuar  calcula las 3 métricas por pregunta. Un fallo se guarda como NaN + mensaje de error, NUNCA como 0.
  resumen  promedios por métrica y configuración y número de casos válidos (eval/resumen.csv).

Regla: solo se evalúan preguntas con "verificada": true en eval/preguntas.json (las verifica el autor contra el PDF).

Uso:
  python -m rag_fds.evaluacion piloto
  python -m rag_fds.evaluacion generar  --config config/topk3.yaml
  python -m rag_fds.evaluacion puntuar  --config config/topk3.yaml
  python -m rag_fds.evaluacion resumen
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import re
import time
import warnings
from importlib import metadata
from pathlib import Path

from rag_fds.config import cargar
from rag_fds.indice import abrir_coleccion, digest_modelo
from rag_fds.rag import cargar_catalogo, responder

warnings.filterwarnings("ignore")

METRICAS = ("faithfulness", "context_precision", "context_recall")
RUN = {"timeout_s": 1800, "max_retries": 3, "max_workers": 1}   # CPU/GPU pequeña: un solo trabajador y timeouts largos


# ------------------------------------------------------------------ evaluador
def crear_metricas(cfg: dict):
    """Devuelve las tres métricas de RAGAS (API con envoltorios de LangChain) con el evaluador local de Ollama."""
    from langchain_ollama import ChatOllama
    from ragas.llms.base import LangchainLLMWrapper
    from ragas.metrics._context_precision import LLMContextPrecisionWithReference
    from ragas.metrics._context_recall import LLMContextRecall
    from ragas.metrics._faithfulness import Faithfulness
    from ragas.run_config import RunConfig

    ev = cfg["evaluador"]
    llm = ChatOllama(model=ev["modelo"], base_url=ev["ollama_url"], temperature=ev["temperature"],
                     num_ctx=ev["num_ctx"], num_predict=ev.get("num_predict", 2048), format="json",
                     client_kwargs={"timeout": RUN["timeout_s"]}, seed=ev.get("seed", 42))
    envoltorio = LangchainLLMWrapper(llm, run_config=RunConfig(timeout=RUN["timeout_s"], max_retries=RUN["max_retries"],
                                                               max_workers=RUN["max_workers"]))
    metricas = {"faithfulness": Faithfulness(llm=envoltorio),
                "context_precision": LLMContextPrecisionWithReference(llm=envoltorio),
                "context_recall": LLMContextRecall(llm=envoltorio)}
    return metricas


def registrar_entorno(cfg: dict) -> dict:
    ev = cfg["evaluador"]
    datos = {
        "evaluador": {"modelo": ev["modelo"], "digest": digest_modelo(ev["ollama_url"], ev["modelo"]), "temperature": ev["temperature"],
                      "num_ctx": ev["num_ctx"], "num_predict": ev.get("num_predict", 2048), "seed": ev.get("seed", 42),
                      "formato_salida": "json (ChatOllama format=json)", "ollama_url": ev["ollama_url"]},
        "ejecucion": {**RUN, "paralelismo": "1 trabajador (evaluación secuencial por métrica)"},
        "versiones": {p: metadata.version(p) for p in ("ragas", "langchain", "langchain-core", "langchain-ollama", "ollama", "datasets")},
        "api_ragas": "ragas.metrics (clases legacy) + ragas.llms.base.LangchainLLMWrapper; en ragas 0.4.4 los envoltorios de LangChain "
                     "están marcados como obsoletos pero funcionan. Embeddings: no se usan (las tres métricas son solo de LLM).",
        "generador": {"modelo": cfg["generador"]["modelo"], "digest": digest_modelo(cfg["generador"]["ollama_url"], cfg["generador"]["modelo"]),
                      "temperature": cfg["generador"]["temperature"], "seed": cfg["generador"]["seed"], "num_ctx": cfg["generador"]["num_ctx"]},
        "embeddings": {"modelo": cfg["embeddings"]["modelo"], "digest": digest_modelo(cfg["embeddings"]["ollama_url"], cfg["embeddings"]["modelo"])},
    }
    return datos


async def _puntuar_una(metrica, muestra, timeout_s: int):
    return await metrica.single_turn_ascore(muestra, timeout=timeout_s)


def quitar_citas(respuesta: str) -> str:
    """Quita las marcas de cita [n] solo para PUNTUAR. Hallazgo del piloto: el evaluador trata "[1][4]" como una afirmación
    más ("El teléfono ... es [1][4]") y la marca como no respaldada, lo que baja la Faithfulness sin que haya un error de
    contenido. La respuesta original (con citas) es la que se guarda y se revisa a mano. Se aplica igual a ambas configuraciones."""
    sin = re.sub(r"\s*\[\d+(?:\s*[,;]\s*\d+)*\]", "", respuesta)
    return re.sub(r"[ \t]+([.,;:])", r"\1", sin).strip()


def puntuar_muestra(metricas: dict, user_input: str, contextos: list[str], respuesta: str, referencia: str) -> dict:
    """Calcula las 3 métricas. Cada fallo -> valor None + mensaje (se guarda como NaN), nunca 0."""
    from ragas.dataset_schema import SingleTurnSample

    muestra = SingleTurnSample(user_input=user_input, retrieved_contexts=contextos, response=quitar_citas(respuesta), reference=referencia)
    salida: dict = {"response_evaluada": muestra.response}
    for nombre in METRICAS:
        t0 = time.perf_counter()
        try:
            v = asyncio.run(_puntuar_una(metricas[nombre], muestra, RUN["timeout_s"]))
            v = float(v)
            if math.isnan(v):
                raise ValueError("RAGAS devolvió NaN")
            salida[nombre], salida[f"error_{nombre}"] = v, ""
        except Exception as e:  # fallo del evaluador (JSON inválido, timeout, ...): se registra, no se convierte en 0
            salida[nombre], salida[f"error_{nombre}"] = None, f"{type(e).__name__}: {str(e)[:300]}"
        salida[f"segundos_{nombre}"] = round(time.perf_counter() - t0, 1)
    return salida


# ------------------------------------------------------------------ datos
def preguntas(solo_verificadas: bool = True) -> list[dict]:
    todas = json.loads(Path("eval/preguntas.json").read_text(encoding="utf-8"))["preguntas"]
    return [p for p in todas if p.get("verificada")] if solo_verificadas else todas


def _fuentes_txt(r: dict) -> list[str]:
    return [f"[{f['n']}] {f['fabricante']} · {f['producto']} · versión {f['version']} · {f['documento']} · pág. {f['pagina']} · sección {f['seccion']}"
            for f in r["fuentes"]]


def correr_rag(pregunta: str, cfg: dict, col, cat) -> dict:
    r = responder(pregunta, cfg, col, cat)
    return {"response": r["respuesta"], "retrieved_contexts": [f["texto"] for f in r["fragmentos"]],
            "fragmentos_meta": [{k: f["meta"][k] for k in ("doc_id", "producto", "pagina_inicio", "pagina_fin", "seccion_num")} for f in r["fragmentos"]],
            "fuentes": _fuentes_txt(r), "citas_invalidas": r["citas_invalidas"], "evidencia_insuficiente": r["evidencia_insuficiente"],
            "filtros": r["filtros"], "t_recuperacion_s": r["t_recuperacion_s"], "t_generacion_s": r["t_generacion_s"],
            "tokens_por_s": r["tokens_por_s"], "tokens_prompt": r["tokens_prompt"], "tokens_generados": r["tokens_generados"]}


# ------------------------------------------------------------------ etapas
def cmd_piloto(args) -> None:
    cfg = cargar("config/topk6.yaml")
    col, cat = abrir_coleccion(cfg), cargar_catalogo(cfg["corpus"]["procesados"])
    casos = json.loads(Path("eval/pilotos_evaluador.json").read_text(encoding="utf-8"))["casos"]
    metricas = crear_metricas(cfg)
    salida = {"entorno": registrar_entorno(cfg), "casos": []}
    for c in casos:
        print(f"\n== piloto {c['id']} ({c['origen']}): {c['pregunta']}", flush=True)
        t0 = time.perf_counter()
        r = correr_rag(c["pregunta"], cfg, col, cat)
        print("respuesta:", r["response"][:300].replace("\n", " "), flush=True)
        p = puntuar_muestra(metricas, c["pregunta"], r["retrieved_contexts"], r["response"], c["respuesta_referencia"])
        print({k: v for k, v in p.items() if not k.startswith("segundos")}, "| s:", {k: v for k, v in p.items() if k.startswith("segundos")}, flush=True)
        salida["casos"].append({"id": c["id"], "origen": c["origen"], "user_input": c["pregunta"], "reference": c["respuesta_referencia"],
                                **r, **p, "segundos_total": round(time.perf_counter() - t0, 1)})
    Path("eval/piloto_evaluador.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nGuardado eval/piloto_evaluador.json")


def cmd_generar(args) -> None:
    cfg = cargar(args.config)
    etiqueta = Path(args.config).stem
    verif = preguntas(True)
    if not verif:
        raise SystemExit("Ninguna pregunta está verificada (\"verificada\": true en eval/preguntas.json). No se evalúa nada hasta que el autor las verifique.")
    col, cat = abrir_coleccion(cfg), cargar_catalogo(cfg["corpus"]["procesados"])
    destino = Path(f"eval/respuestas_{etiqueta}.json")
    previo = {x["id"]: x for x in json.loads(destino.read_text(encoding="utf-8"))} if destino.exists() else {}
    for p in verif:
        if p["id"] in previo and not args.rehacer:
            continue
        print(f"[{etiqueta}] {p['id']} {p['pregunta'][:80]}", flush=True)
        r = correr_rag(p["pregunta"], cfg, col, cat)
        previo[p["id"]] = {"id": p["id"], "tipo": p["tipo"], "config": etiqueta, "top_k": cfg["top_k"], "user_input": p["pregunta"],
                           "reference": p.get("respuesta_referencia"), **r}
        destino.write_text(json.dumps(list(previo.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    # las sin respuesta se separan: no se puntúan con RAGAS, se revisan a mano
    sin = [x for x in previo.values() if x["tipo"] == "sin_respuesta"]
    Path(f"eval/sin_respuesta_{etiqueta}.json").write_text(json.dumps(sin, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Respuestas guardadas en {destino} ({len(previo)} preguntas, {len(sin)} sin respuesta)")


def cmd_puntuar(args) -> None:
    cfg = cargar(args.config)
    etiqueta = Path(args.config).stem
    resp = [x for x in json.loads(Path(f"eval/respuestas_{etiqueta}.json").read_text(encoding="utf-8")) if x["tipo"] != "sin_respuesta"]
    destino = Path(f"eval/resultados_{etiqueta}.json")
    hechos = {x["id"]: x for x in json.loads(destino.read_text(encoding="utf-8"))["resultados"]} if destino.exists() else {}
    entorno = registrar_entorno(cfg)
    metricas = crear_metricas(cfg)
    t_ini = time.perf_counter()
    for x in resp:
        previo = hechos.get(x["id"])
        if previo and not args.reintentar_errores:
            continue
        if previo and args.reintentar_errores and all(previo.get(f"error_{m}", "") == "" for m in METRICAS):
            continue
        print(f"[{etiqueta}] puntuando {x['id']} ...", flush=True)
        p = puntuar_muestra(metricas, x["user_input"], x["retrieved_contexts"], x["response"], x["reference"])
        hechos[x["id"]] = {**x, **p}
        print("   ", {k: p[k] for k in METRICAS}, {k: p[k] for k in p if k.startswith("error_") and p[k]}, flush=True)
        destino.write_text(json.dumps({"entorno": entorno, "resultados": list(hechos.values())}, ensure_ascii=False, indent=2), encoding="utf-8")
    seg = round(time.perf_counter() - t_ini)
    datos = json.loads(destino.read_text(encoding="utf-8"))
    datos["segundos_evaluacion_esta_corrida"] = seg
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    # CSV
    columnas = ["id", "tipo", "config", "top_k", "user_input", "response", "reference", "fuentes", "retrieved_contexts",
                *METRICAS, *[f"error_{m}" for m in METRICAS], "t_recuperacion_s", "t_generacion_s"]
    with open(f"eval/resultados_{etiqueta}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        for r in datos["resultados"]:
            fila = dict(r)
            fila["fuentes"] = json.dumps(r["fuentes"], ensure_ascii=False)
            fila["retrieved_contexts"] = json.dumps(r["retrieved_contexts"], ensure_ascii=False)
            for m in METRICAS:
                fila[m] = "NaN" if r.get(m) is None else r[m]
            w.writerow(fila)
    print(f"Listo ({seg} s). Resultados en eval/resultados_{etiqueta}.json/.csv")


def cmd_resumen(args) -> None:
    filas = []
    for etiqueta in ("topk3", "topk6"):
        ruta = Path(f"eval/resultados_{etiqueta}.json")
        if not ruta.exists():
            continue
        res = json.loads(ruta.read_text(encoding="utf-8"))["resultados"]
        fila = {"config": etiqueta, "top_k": res[0]["top_k"] if res else "", "preguntas": len(res)}
        for m in METRICAS:
            vals = [r[m] for r in res if r.get(m) is not None]
            fila[f"{m}_promedio"] = round(sum(vals) / len(vals), 4) if vals else "NaN"
            fila[f"{m}_casos_validos"] = len(vals)
        filas.append(fila)
    with open("eval/resumen.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    for fila in filas:
        print(fila)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("piloto")
    for n in ("generar", "puntuar"):
        s = sub.add_parser(n)
        s.add_argument("--config", required=True)
        s.add_argument("--rehacer", action="store_true", help="(generar) vuelve a correr preguntas ya guardadas")
        s.add_argument("--reintentar-errores", action="store_true", help="(puntuar) repite las preguntas con algún error")
    sub.add_parser("resumen")
    args = ap.parse_args()
    {"piloto": cmd_piloto, "generar": cmd_generar, "puntuar": cmd_puntuar, "resumen": cmd_resumen}[args.cmd](args)


if __name__ == "__main__":
    main()
