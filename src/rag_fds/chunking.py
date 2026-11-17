"""Chunking guiado por la estructura de la FDS.

1. Se recorre documento.md siguiendo los encabezados de sección (secciones.py); cada fragmento pertenece a UNA sección.
2. Dentro de una sección el texto se corta por tamaño (~800 caracteres, solape ~150) en límites de frase.
3. Las tablas no se parten: cada tabla es su propio fragmento; si excede el máximo se divide por filas repitiendo el encabezado.
4. Cada fragmento lleva un encabezado corto (fabricante · producto · versión · año · sección) y, en sus metadatos,
   documento, páginas, sección e imágenes de las mismas páginas (misma página; no se afirma relación con tablas).

Mitigaciones de errores de extracción (ver verificacion/errores_extraccion.md):
  - títulos repetidos del encabezado de página se ignoran;
  - ideogramas leídos por el OCR a partir de íconos (日, 回, 新) se eliminan del texto;
  - encabezados de sección fundidos en un párrafo (FDS 100/101, marca de agua) se detectan dentro del párrafo;
  - se decodifican los escapes de Docling (&amp;, \\_).

Uso: python -m rag_fds.chunking --config config/base.yaml --salida indice/chunks.jsonl
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from rag_fds.config import cargar
from rag_fds.secciones import ENCABEZADO, SECCIONES, clasificar, limpiar_linea, paginas_md

RE_IMAGEN = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
RE_IDEOGRAMA = re.compile(r"[\u2E80-\u9FFF\uAC00-\uD7AF\uFF00-\uFFEF]")
RE_MARCA_AGUA = re.compile(r"\bCOPIA CONTROLADA\b")
# Encabezado de sección fundido dentro de un párrafo: "... SECCIÓN 7: MANIPULACIÓN Y ALMACENAMIENTO 7.1 ..."
RE_ENCABEZADO_EN_LINEA = re.compile(r"SECCI[ÓO]N\s+\d{1,2}\s*[:.]\s*[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ ,/\-]{5,}")


def limpiar_texto(t: str) -> str:
    t = html.unescape(t.replace("\\_", "_"))
    t = RE_IDEOGRAMA.sub("", t)
    t = RE_MARCA_AGUA.sub("", t)
    return re.sub(r"[ \t]+", " ", t).strip()


def colapsar_celdas(fila: str) -> str:
    """Docling repite el texto de las celdas combinadas en cada columna que abarcan; se deja una sola copia
    de celdas idénticas consecutivas (no se pierde información, solo el ruido repetido)."""
    if re.match(r"^\|[\s:\-|]+\|$", fila.replace(" ", "")):
        # separador de la tabla Markdown: Docling lo rellena con cientos de guiones (ancho de columna); se compacta
        return re.sub(r"\s*-{3,}\s*", "---", fila)
    celdas = [c.strip() for c in fila.strip().strip("|").split("|")]
    salida = []
    for c in celdas:
        if not (salida and c and c == salida[-1]):
            salida.append(c)
    return "| " + " | ".join(salida) + " |"


def titulos_repetidos(paginas: dict[int, str]) -> set[str]:
    """Encabezados `##` idénticos en 3 o más páginas (nombre del producto en la cabecera de página): son ruido."""
    from collections import Counter

    c = Counter()
    for t in paginas.values():
        for l in {limpiar_linea(x) for x in t.splitlines() if x.lstrip().startswith("#")}:
            c[l] += 1
    return {l for l, n in c.items() if n >= 3 and not ENCABEZADO.match(l)}


def seccion_de_linea(linea: str) -> int | None:
    """Sección que abre esta línea, si es un encabezado de sección (también dentro de celdas de tabla)."""
    for celda in (linea.split("|") if "|" in linea else [linea]):
        c = limpiar_linea(celda)
        m = ENCABEZADO.match(c) if c else None
        if m and 1 <= int(m.group(1)) <= 16:
            n = clasificar(m.group("t"))
            if n:
                return n
    return None


def dividir_frases(texto: str, tam: int) -> list[str]:
    """Divide en frases; las que superan `tam` se parten por palabras."""
    partes = [p.strip() for p in re.split(r"(?<=[.;:!?])\s+", texto) if p.strip()]
    salida = []
    for p in partes:
        while len(p) > tam * 1.5:
            corte = p.rfind(" ", 0, tam)
            corte = corte if corte > tam * 0.5 else tam
            salida.append(p[:corte].strip())
            p = p[corte:].strip()
        if p:
            salida.append(p)
    return salida


def bloques_documento(md: str) -> list[dict]:
    """Convierte el Markdown en bloques ordenados: {tipo: texto|tabla, seccion, pagina, texto, imagenes}."""
    paginas = paginas_md(md)
    ignorar = titulos_repetidos(paginas)
    bloques: list[dict] = []
    seccion = 0                      # 0 = portada/encabezado antes de la sección 1
    vistas: set[int] = set()         # secciones cuyo encabezado ya se emitió ("(continúa)" no se repite)
    for pag in sorted(paginas):
        lineas = paginas[pag].splitlines()
        i = 0
        parrafo: list[str] = []

        def cerrar_parrafo():
            nonlocal parrafo
            if parrafo:
                txt = limpiar_texto(" ".join(parrafo))
                if txt:
                    bloques.append({"tipo": "texto", "seccion": seccion, "pagina": pag, "texto": txt})
                parrafo = []

        while i < len(lineas):
            l = lineas[i]
            s = l.strip()
            if not s or s.startswith("<!--") or RE_IMAGEN.fullmatch(s):
                cerrar_parrafo() if not s else None
                i += 1
                continue
            if s.startswith("|"):                       # tabla: líneas consecutivas
                cerrar_parrafo()
                j = i
                while j < len(lineas) and lineas[j].strip().startswith("|"):
                    j += 1
                filas = [colapsar_celdas(limpiar_texto(x)) for x in lineas[i:j]]
                nueva = next((n for n in (seccion_de_linea(x) for x in filas) if n), None)
                if nueva:
                    seccion = nueva
                    vistas.add(nueva)
                if len(filas) >= 3 and re.match(r"^\|[\s:\-|]+\|$", filas[1].replace(" ", "")):
                    bloques.append({"tipo": "tabla", "seccion": seccion, "pagina": pag, "filas": filas})
                else:                                   # tabla malformada: se trata como texto
                    bloques.append({"tipo": "texto", "seccion": seccion, "pagina": pag,
                                    "texto": " ".join(f.strip("| ").replace(" | ", "; ") for f in filas)})
                i = j
                continue
            # párrafo o encabezado
            texto = limpiar_texto(s.lstrip("#").strip()) if s.startswith("#") else limpiar_texto(s)
            if s.startswith("#") and limpiar_linea(s) in ignorar:
                i += 1
                continue
            # encabezados de sección fundidos en un párrafo: se separan
            partes = [texto]
            m = RE_ENCABEZADO_EN_LINEA.search(texto)
            if m and m.start() > 0:
                partes = [texto[:m.start()].strip(), texto[m.start():].strip()]
            for k, parte in enumerate(partes):
                if not parte:
                    continue
                n = seccion_de_linea(parte) if (s.startswith("#") or k == 1 or len(parte) < 160) else None
                if n and (s.startswith("#") or k == 1 or ENCABEZADO.match(limpiar_linea(parte))):
                    cerrar_parrafo()
                    seccion = n
                    if n not in vistas:                 # solo la primera vez; "(continúa)" no se repite
                        vistas.add(n)
                        bloques.append({"tipo": "texto", "seccion": seccion, "pagina": pag, "texto": parte})
                    continue
                if s.startswith("#"):                   # subtítulo: abre un párrafo nuevo
                    cerrar_parrafo()
                    bloques.append({"tipo": "texto", "seccion": seccion, "pagina": pag, "texto": parte})
                else:
                    parrafo.append(parte)
            i += 1
        cerrar_parrafo()
    return bloques


def dividir_tabla(filas: list[str], max_chars: int) -> list[list[str]]:
    """Una tabla cabe en un fragmento; si excede max_chars se parte por filas repitiendo encabezado y separador."""
    if sum(len(f) + 1 for f in filas) <= max_chars:
        return [filas]
    enc, cuerpo = filas[:2], filas[2:]
    grupos, actual, largo = [], [], sum(len(f) + 1 for f in enc)
    for f in cuerpo:
        if actual and largo + len(f) + 1 > max_chars:
            grupos.append(enc + actual)
            actual, largo = [], sum(len(x) + 1 for x in enc)
        actual.append(f)
        largo += len(f) + 1
    if actual:
        grupos.append(enc + actual)
    return grupos


def fragmentar(bloques: list[dict], cfg: dict) -> list[dict]:
    """Aplica tamaño/solape a los bloques de texto (por sección) y deja las tablas enteras."""
    tam, solape, max_tabla, minimo = cfg["tam_objetivo"], cfg["solape"], cfg["tam_max_tabla"], cfg["min_chars"]
    frag: list[dict] = []
    buf: list[tuple[str, int]] = []       # (frase, página)
    sec_buf = None
    nuevas = 0                            # frases añadidas desde el último vaciado (el solape no cuenta)

    def vaciar(final: bool):
        nonlocal buf, nuevas
        if not buf:
            return
        texto = " ".join(t for t, _ in buf).strip()
        if nuevas and len(texto) >= minimo:
            frag.append({"tipo": "texto", "seccion": sec_buf, "texto": texto,
                         "p_ini": min(p for _, p in buf), "p_fin": max(p for _, p in buf)})
        nuevas = 0
        if final:
            buf = []
            return
        # solape: últimas frases que sumen <= solape caracteres
        resto, total = [], 0
        for t, p in reversed(buf):
            if total + len(t) > solape and resto:
                break
            resto.insert(0, (t, p))
            total += len(t) + 1
        buf = resto if total <= solape * 1.6 else []

    for b in bloques:
        if b["tipo"] == "tabla":
            vaciar(True)
            for grupo in dividir_tabla(b["filas"], max_tabla):
                frag.append({"tipo": "tabla", "seccion": b["seccion"], "texto": "\n".join(grupo),
                             "p_ini": b["pagina"], "p_fin": b["pagina"]})
            continue
        if b["seccion"] != sec_buf:
            vaciar(True)
            sec_buf = b["seccion"]
        for frase in dividir_frases(b["texto"], tam):
            largo = sum(len(t) + 1 for t, _ in buf)
            if buf and largo + len(frase) > tam:
                vaciar(False)
            buf.append((frase, b["pagina"]))
            nuevas += 1
    vaciar(True)
    return frag


def cabecera(meta: dict, seccion: int) -> str:
    nombre = SECCIONES[seccion][0] if seccion in SECCIONES else "Encabezado del documento"
    fab = meta.get("fabricante") or "fabricante no consta"
    ver = meta.get("version") or "versión no consta"
    sec = f"Sección {seccion}: {nombre}" if seccion else nombre
    return f"[{fab} · {meta['producto']} · versión {ver} · FDS {meta.get('anio_carpeta')} · {sec}]"


def chunks_de_documento(dir_doc: Path, cfg: dict) -> list[dict]:
    meta = json.loads((dir_doc / "meta.json").read_text(encoding="utf-8"))
    bloques = bloques_documento((dir_doc / "documento.md").read_text(encoding="utf-8"))
    imgs = json.loads((dir_doc / "imagenes.json").read_text(encoding="utf-8")).get("imagenes", [])
    por_pagina: dict[int, list[str]] = {}
    for im in imgs:
        por_pagina.setdefault(im["pagina"], []).append(f"{dir_doc.as_posix()}/{im['archivo']}")
    salida = []
    for n, f in enumerate(fragmentar(bloques, cfg), 1):
        cab = cabecera(meta, f["seccion"])
        imagenes = [r for p in range(f["p_ini"], f["p_fin"] + 1) for r in por_pagina.get(p, [])]
        sec = f["seccion"]
        salida.append({
            "id": f"{meta['doc_id']}::{n:04d}",
            "texto": f"{cab}\n{f['texto']}",
            "cuerpo": f["texto"],
            "tipo": f["tipo"],
            "meta": {
                "doc_id": meta["doc_id"], "fabricante": meta.get("fabricante") or "", "producto": meta["producto"],
                "version": meta.get("version") or "", "fecha_revision": meta.get("fecha_revision") or "",
                "anio": str(meta.get("anio_carpeta") or ""), "archivo": meta["nombre_mostrado"],
                "archivo_original": meta["archivo_original"], "pagina_inicio": f["p_ini"], "pagina_fin": f["p_fin"],
                "seccion_num": sec, "seccion_nombre": SECCIONES[sec][0] if sec in SECCIONES else "Encabezado del documento",
                "tipo": f["tipo"], "imagenes": json.dumps(imagenes, ensure_ascii=False),
            },
        })
    return salida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/base.yaml")
    ap.add_argument("--salida", type=Path, default=Path("indice/chunks.jsonl"))
    args = ap.parse_args()
    cfg = cargar(args.config)
    raiz = Path(cfg["corpus"]["procesados"])
    todos = []
    for d in sorted(raiz.iterdir()):
        if (d / "meta.json").exists():
            todos.extend(chunks_de_documento(d, cfg["chunking"]))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        for c in todos:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    largos = sorted(len(c["texto"]) for c in todos)
    por_tipo = {t: sum(1 for c in todos if c["tipo"] == t) for t in ("texto", "tabla")}
    print(f"{len(todos)} fragmentos {por_tipo}; largo mediano {largos[len(largos) // 2]}, p95 {largos[int(len(largos) * .95)]}, máx {largos[-1]}")


if __name__ == "__main__":
    main()
