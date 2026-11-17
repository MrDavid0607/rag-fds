"""Índice vectorial: embeddings con bge-m3 (Ollama) + Chroma persistente.

Uso:  python -m rag_fds.indice --config config/base.yaml [--reconstruir]
Lee indice/chunks.jsonl (generado por chunking.py) y escribe indice/chroma/ + indice/manifiesto.json con los parámetros,
el digest del modelo de embeddings y los tiempos.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

from rag_fds.config import cargar


def embeber(textos: list[str], cfg_emb: dict, reintentos: int = 3) -> list[list[float]]:
    """Embeddings por lotes con Ollama (/api/embed). Los vectores se normalizan en Chroma por la métrica coseno."""
    url = cfg_emb["ollama_url"].rstrip("/") + "/api/embed"
    for intento in range(reintentos):
        try:
            r = requests.post(url, json={"model": cfg_emb["modelo"], "input": textos, "truncate": False,
                                         "keep_alive": "15m"}, timeout=600)
            r.raise_for_status()
            return r.json()["embeddings"]
        except Exception:
            if intento == reintentos - 1:
                raise
            time.sleep(3)


def digest_modelo(url: str, modelo: str) -> str:
    try:
        tags = requests.get(url.rstrip("/") + "/api/tags", timeout=30).json()["models"]
        for m in tags:
            if m["name"] == modelo or m["name"] == modelo + ":latest" or m["model"] == modelo:
                return m["digest"]
    except Exception:
        pass
    return ""


def abrir_coleccion(cfg: dict, crear: bool = False):
    import chromadb

    cliente = chromadb.PersistentClient(path=cfg["indice"]["ruta"])
    if crear:
        try:
            cliente.delete_collection(cfg["indice"]["coleccion"])
        except Exception:
            pass
        return cliente.create_collection(cfg["indice"]["coleccion"], metadata={"hnsw:space": cfg["indice"]["metrica"]})
    return cliente.get_collection(cfg["indice"]["coleccion"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/base.yaml")
    ap.add_argument("--chunks", type=Path, default=Path("indice/chunks.jsonl"))
    args = ap.parse_args()
    cfg = cargar(args.config)
    chunks = [json.loads(l) for l in open(args.chunks, encoding="utf-8")]
    col = abrir_coleccion(cfg, crear=True)

    t0 = time.perf_counter()
    lote = cfg["embeddings"]["lote"]
    for i in range(0, len(chunks), lote):
        grupo = chunks[i:i + lote]
        vectores = embeber([c["texto"] for c in grupo], cfg["embeddings"])
        col.add(ids=[c["id"] for c in grupo], embeddings=vectores, documents=[c["texto"] for c in grupo],
                metadatas=[c["meta"] for c in grupo])
        if (i // lote) % 20 == 0:
            print(f"{i + len(grupo)}/{len(chunks)}", flush=True)
    seg = time.perf_counter() - t0

    manifiesto = {
        "n_fragmentos": col.count(), "chunking": cfg["chunking"],
        "embeddings": {**cfg["embeddings"], "digest": digest_modelo(cfg["embeddings"]["ollama_url"], cfg["embeddings"]["modelo"])},
        "indice": cfg["indice"], "segundos_indexado": round(seg, 1),
        "fragmentos_por_segundo": round(len(chunks) / seg, 1),
    }
    Path("indice/manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifiesto, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
