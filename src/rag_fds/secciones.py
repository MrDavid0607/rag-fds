"""Detección de las 16 secciones de una FDS y su estado, sin inferir nada.

Estados por sección:
  presente              el encabezado está en el Markdown (documento.md).
  fallo_extraccion      el encabezado aparece en el texto crudo del PDF (pypdfium2) pero no en el Markdown.
  ausente_en_original   no está en el Markdown ni en el texto crudo -> el autor la revisa en el PDF.

Un encabezado cuenta solo si lleva el NÚMERO de sección y palabras clave de su título (los títulos varían entre
fabricantes). Las subsecciones (1.1, 2.3 ...) no cuentan como encabezado de sección.

Uso: python -m rag_fds.secciones --procesados data/processed --raw "data/raw/FDS EVALUADAS" --csv verificacion/secciones.csv
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path

SECCIONES = {
    1: ("Identificación del producto y de la empresa", r"identifica"),
    2: ("Identificación de peligros", r"peligro"),
    3: ("Composición / información sobre los componentes", r"composici|componentes|ingredientes"),
    4: ("Primeros auxilios", r"primeros\s+auxilios"),
    5: ("Medidas de lucha contra incendios", r"incendio|extinci"),
    6: ("Medidas en caso de vertido accidental", r"vertido|derrame|liberaci[oó]n(?:es)?\s+accidental|dispersi[oó]n"),
    7: ("Manipulación y almacenamiento", r"manipula|almacen"),
    8: ("Controles de exposición / protección personal", r"exposici|protecci[oó]n\s+(?:personal|individual)|controles"),
    9: ("Propiedades físicas y químicas", r"propiedades|f[ií]sic"),
    10: ("Estabilidad y reactividad", r"estabilidad|reactividad"),
    11: ("Información toxicológica", r"toxicol"),
    12: ("Información ecológica", r"ecol[oó]g"),
    13: ("Consideraciones relativas a la eliminación", r"eliminaci|disposici|desecho|residuos"),
    14: ("Información relativa al transporte", r"transporte"),
    15: ("Información reglamentaria", r"reglament|normativ|regulat"),
    16: ("Otra información", r"otra\s+informaci|otros\s+datos|informaci[oó]n\s+adicional|otras\s+informaci"),
}

# línea de encabezado: [Sección] N  [.:-)]  Título    (N de 1 a 16, sin que siga ".d" -> eso es subsección)
ENCABEZADO = re.compile(r"^\W{0,4}(?:secci[oó]n|section)?\s*(\d{1,2})(?!\d)(?!\s*[.,]\s*\d)\s*[.:\-–—)]*\s*(?P<t>[^\n]{0,160})$",
                        re.IGNORECASE)


def limpiar_linea(l: str) -> str:
    l = html.unescape(l.replace("\\_", "_"))
    l = re.sub(r"<!--.*?-->|!\[[^\]]*\]\([^)]*\)", " ", l)
    l = l.replace("|", " ").replace("*", " ").replace("#", " ")
    return re.sub(r"\s+", " ", l).strip()


def clasificar(titulo: str) -> int | None:
    """Sección canónica (1-16) a la que corresponde un título, según sus palabras clave.

    La identidad de la sección la da el TÍTULO, no el número: las FDS antiguas (norma NTC) numeran en otro
    orden (p. ej. 2 = composición, 3 = identificación de riesgos). El orden de las reglas resuelve choques
    ("identificación de riesgos" no es la sección 1; "ecotoxicológica" no es la 11).
    """
    t = titulo.lower()
    # "peligros"/"riesgos" (sección 2) pero no "sustancia química peligrosa" (título de la sección 1 en FDS Sika)
    if re.search(r"\b(peligros?|riesgos?)\b", t):
        return 2
    if re.search(r"ecol[oó]g|ecotox", t):
        return 12
    for n in (4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 3, 1):
        if re.search(SECCIONES[n][1], t):
            return n
    return None


def encabezados(paginas: dict[int, str]) -> dict[int, tuple[int, str, int]]:
    """Devuelve {sección_canónica: (página, línea, número_en_documento)}: primera aparición válida de cada una."""
    hallados: dict[int, tuple[int, str, int]] = {}
    for pag in sorted(paginas):
        # cada celda de tabla cuenta como una línea (algunas FDS ponen el encabezado dentro de una tabla)
        lineas = [limpiar_linea(c) for l in paginas[pag].splitlines() for c in (l.split("|") if "|" in l else [l])]
        lineas = [l for l in lineas if l]
        for i, l in enumerate(lineas):
            m = ENCABEZADO.match(l)
            if not m or not (1 <= int(m.group(1)) <= 16):
                continue
            num = int(m.group(1))
            titulo = m.group("t")
            n = clasificar(titulo)
            if n is None and re.match(r"\W{0,4}(secci[oó]n|section)", l, re.IGNORECASE) and i + 1 < len(lineas):
                n = clasificar(titulo + " " + lineas[i + 1])  # "SECCIÓN 4:" / "PRIMEROS AUXILIOS" en dos líneas
            if n is not None and n not in hallados:
                hallados[n] = (pag, l[:140], num)
    return hallados


def paginas_md(md: str) -> dict[int, str]:
    partes = re.split(r"<!-- pagina: (\d+) -->", md)
    return {int(partes[i]): partes[i + 1] for i in range(1, len(partes), 2)}


def texto_crudo_pdf(pdf: Path) -> dict[int, str]:
    import pypdfium2 as pdfium

    d = pdfium.PdfDocument(str(pdf))
    return {i + 1: d[i].get_textpage().get_text_range().replace("\r", "") for i in range(len(d))}


def sin_numero(paginas: dict[int, str], solo_titulos_md: bool) -> dict[int, tuple[int, str, int]]:
    """Segunda pasada para FDS que no numeran sus secciones: una línea corta cuyo texto ES el título canónico
    (p. ej. "Primeros auxilios:"). Se marca con número_en_documento = 0 (sin número)."""
    hallados: dict[int, tuple[int, str, int]] = {}
    for pag in sorted(paginas):
        for l in paginas[pag].splitlines():
            if solo_titulos_md and not l.lstrip().startswith("#"):
                continue
            t = limpiar_linea(l).rstrip(":. ")
            if 1 <= len(t.split()) <= 6 and not re.match(r"\d", t):
                n = clasificar(t)
                if n is not None and n not in hallados:
                    hallados[n] = (pag, t[:140] + " (sin número)", 0)
    return hallados


def estados_doc(md: str, crudo: dict[int, str]) -> list[dict]:
    pm = paginas_md(md)
    en_md = encabezados(pm)
    en_crudo = encabezados(crudo)
    for n, v in sin_numero(pm, True).items():
        en_md.setdefault(n, v)
    for n, v in sin_numero(crudo, False).items():
        en_crudo.setdefault(n, v)
    filas = []
    for n, (nombre, _) in SECCIONES.items():
        if n in en_md:
            estado, (pag, ev, num) = "presente", en_md[n]
        elif n in en_crudo:
            estado, (pag, ev, num) = "fallo_extraccion", en_crudo[n]
        else:
            estado, pag, ev, num = "ausente_en_original", "", "", ""
        filas.append({"seccion": n, "nombre": nombre, "estado": estado, "pagina": pag,
                      "numero_en_documento": num, "evidencia": ev})
    return filas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procesados", type=Path, default=Path("data/processed"))
    ap.add_argument("--raw", type=Path, default=Path("data/raw/FDS EVALUADAS"))
    ap.add_argument("--csv", type=Path, default=Path("verificacion/secciones.csv"))
    args = ap.parse_args()

    pdfs = {p.name: p for p in args.raw.rglob("*.pdf")}
    filas = []
    for d in sorted(args.procesados.iterdir()):
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        md = (d / "documento.md").read_text(encoding="utf-8")
        est = estados_doc(md, texto_crudo_pdf(pdfs[meta["archivo_original"]]))
        for e in est:
            filas.append({"doc_id": meta["doc_id"], **e, "revisado_por_autor": ""})
        # copia por ficha, útil para el chunking (qué sección empieza en qué página)
        (d / "secciones.json").write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    from collections import Counter
    print(dict(Counter(f["estado"] for f in filas)))


if __name__ == "__main__":
    main()
