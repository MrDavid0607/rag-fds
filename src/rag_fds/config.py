"""Carga de configuración con herencia simple: un YAML puede declarar `hereda: otro.yaml` y sobrescribir claves.

Regla del proyecto: topk3.yaml y topk6.yaml solo pueden cambiar `top_k`. `verificar_solo_topk` lo comprueba.
"""
from __future__ import annotations

from pathlib import Path

import yaml


def _fusionar(base: dict, extra: dict) -> dict:
    out = dict(base)
    for k, v in extra.items():
        out[k] = _fusionar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def cargar(ruta: str | Path) -> dict:
    ruta = Path(ruta)
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    padre = datos.pop("hereda", None)
    if padre:
        datos = _fusionar(cargar(ruta.parent / padre), datos)
    return datos


def verificar_solo_topk(ruta_a: str | Path, ruta_b: str | Path) -> None:
    """Falla si dos configuraciones difieren en algo distinto de top_k."""
    a, b = cargar(ruta_a), cargar(ruta_b)
    a.pop("top_k", None)
    b.pop("top_k", None)
    if a != b:
        raise ValueError("Las configuraciones difieren en algo más que top_k")
