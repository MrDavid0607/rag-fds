"""Metadatos de contenido de cada FDS: fabricante, producto, código, versión y fecha de revisión.

Regla del proyecto: NADA se infiere. Cada dato se toma de un texto que aparece en la ficha y se guarda junto
con su evidencia (fragmento literal, página y fuente). Si no aparece, el campo queda vacío y se anota.

Fuentes de texto, en este orden:
  1. Texto crudo del PDF (pypdfium2): Docling descarta encabezados y pies de página del Markdown, y en muchas
     FDS la versión y la fecha están justo ahí ("Versión: 1  Página 1/8"). Es la fuente más fiel para ellos.
  2. Markdown extraído (documento.md).
El nombre de archivo NO es fuente de contenido; si trae "(Versión N)" se guarda aparte como
`version_en_nombre_archivo` (procedencia, no dato de la ficha).

Uso:  python -m rag_fds.metadatos --procesados data/processed --raw "data/raw/FDS EVALUADAS" --csv verificacion/metadatos.csv
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path

# (etiqueta canónica, patrón que debe aparecer literalmente en el texto de la ficha)
FABRICANTES = [
    ("Pintuco", r"\bpintuco\b"),
    ("Corona", r"\bcorona\b|\bcorlanc\b"),
    ("PPG", r"\bPPG\b"),
    ("Pintuland", r"\bpintuland\b"),
    ("INVESA", r"\binvesa\b|\bsapolin\b"),
    ("Sika", r"\bsika\b"),
    ("AkzoNobel", r"\bakzo\s?nobel\b|\baksonobel\b|\bglobal de pinturas\b"),
    ("Bler", r"\bbler\b"),
]

# Valores que son etiquetas de otro campo y no un nombre de producto
ETIQUETA = re.compile(r"^(c[oó]digo|fecha|uso|tipo|otros|no disponible|identificador|n[uú]mero|sds|versi[oó]n|"
                      r"nombre|compa[nñ][ií]a|tel[eé]fono|datos|secci[oó]n|\d+\.\d+)\b", re.IGNORECASE)
GENERICO = re.compile(r"(ficha|hoja)\s+de\s+datos|seguridad|^secci[oó]n|^versi[oó]n|^fecha|<!--|!\[|^[\W_]*(x|international)([\W_]+(x|international))*[\W_]*$|"
                      r"^[\W_]*$|^p[aá]gina|^\|", re.IGNORECASE)

CLAVES_PRODUCTO = [
    r"Identificador SGA del producto\s*:?\s*(?P<v>[^\n]+)",
    r"Nombre del producto\s*:?\s*\n*\s*:?\s*(?P<v>[^\n]+)",
    r"Identificador del producto\s*:?\s*\n*\s*:?\s*(?P<v>[^\n]+)",
    r"Nombre comercial\s*:?\s*(?P<v>[^\n]+)",
]
CLAVES_CODIGO = [
    r"C[oó]digo (?:del )?producto\s*:?\s*\n*\s*:?\s*(?P<v>[A-Za-z0-9\-/.]*\d[A-Za-z0-9\-/.]*)",
    r"\bSDS code\s*\n*\s*:?\s*(?P<v>[A-Za-z0-9\-/.]*\d[A-Za-z0-9\-/.]*)",
    r"N[uú]mero de HDS\s*:?\s*(?P<v>\d[\w\-/.]*)",
    r"\bMSDS no\.?\s*:?\s*(?P<v>\d[\w\-/.]*)",
]
CLAVES_VERSION = [
    r"Versi[oó]n\s*(?:n[uú]mero\s*)?:?\s*(?P<v>\d+(?:[.,]\d+)*)",
    r"Revisi[oó]n\s*(?:n[uú]mero\s*)?:\s*(?P<v>\d+(?:[.,]\d+)*)\b",
    r"Edici[oó]n\s*:\s*(?P<v>\d+(?:[.,]\d+)*)",
]
FECHA = (r"(?P<v>\d{1,4}[/\-.]\d{1,2}[/\-.]\d{1,4}|\d{1,2}\s+(?:de\s+)?[A-Za-zéÉ]+\.?\s+(?:de\s+)?\d{4}|"
         r"[A-Za-zéÉ]+\s+(?:de\s+)?\d{1,2}?,?\s*(?:de\s+)?\d{4})")
CLAVES_FECHA = [
    rf"Fecha de (?:la )?revisi[oó]n\s*:?\s*{FECHA}",
    rf"Fecha de (?:la )?(?:emisi[oó]n|edici[oó]n|elaboraci[oó]n|actualizaci[oó]n|publicaci[oó]n|expedici[oó]n)\s*:?\s*{FECHA}",
]


def limpiar(t: str) -> str:
    """Quita escapes de Docling (&amp;, \\_) y espacios repetidos."""
    return re.sub(r"[ \t]+", " ", html.unescape(t.replace("\\_", "_")))


def _buscar(patrones: list[str], texto: str, valido=lambda v: True) -> tuple[str, str] | None:
    for p in patrones:
        for m in re.finditer(p, texto, flags=re.IGNORECASE):
            valor = re.sub(r"\s+", " ", m.group("v")).strip(" |:*_#")
            if valor and valido(valor):
                return valor, re.sub(r"\s+", " ", m.group(0)).strip()
    return None


def _paginas_md(md: str) -> dict[int, str]:
    partes = re.split(r"<!-- pagina: (\d+) -->", md)
    return {int(partes[i]): limpiar(partes[i + 1]) for i in range(1, len(partes), 2)}


def texto_crudo_pdf(pdf: Path) -> dict[int, str]:
    import pypdfium2 as pdfium

    d = pdfium.PdfDocument(str(pdf))
    return {i + 1: limpiar(d[i].get_textpage().get_text_range().replace("\r", "")) for i in range(len(d))}


def _titulo_pagina1(pagina1: str, valido=lambda v: True) -> tuple[str, str] | None:
    """Respaldo: primera línea no genérica de la página 1 (suele ser el nombre del producto)."""
    for linea in pagina1.splitlines():
        t = linea.strip().lstrip("#").strip()
        if len(t) >= 3 and re.search(r"[A-Za-zÁÉÍÓÚáéíóú]", t) and not GENERICO.search(t) and valido(t):
            return t, f"título de la página 1: {t}"
    return None


def extraer(md_paginas: dict[int, str], crudo: dict[int, str]) -> dict:
    md_total = "\n".join(md_paginas.values())
    crudo_total = "\n".join(f"\n@@P{n}@@\n{t}" for n, t in crudo.items())
    res: dict = {"evidencia": {}}
    notas: list[str] = []

    def pagina_de(texto_total: str, fragmento: str) -> int | None:
        i = texto_total.find(fragmento)
        if i < 0:
            return None
        ult = re.findall(r"@@P(\d+)@@", texto_total[:i])
        return int(ult[-1]) if ult else None

    # Fabricante: debe aparecer literalmente en el texto; manda el más mencionado, el resto va a la nota
    base = md_total + "\n" + "\n".join(crudo.values())
    hallados = []
    for etiqueta, patron in FABRICANTES:
        n = len(re.findall(patron, base, flags=re.IGNORECASE))
        if n:
            m = re.search(patron, base, flags=re.IGNORECASE)
            hallados.append((etiqueta, m.group(0), n))
    hallados.sort(key=lambda h: -h[2])
    if hallados:
        res["fabricante"] = hallados[0][0]
        res["evidencia"]["fabricante"] = f'"{hallados[0][1]}" ({hallados[0][2]} menciones)'
        if len(hallados) > 1:
            notas.append("fabricantes mencionados: " + ", ".join(f"{h[0]} x{h[2]}" for h in hallados))
    else:
        res["fabricante"] = ""
        notas.append("fabricante: no aparece en el contenido")

    # Producto: etiqueta en el Markdown (páginas 1-2); si no, título de la página 1
    cab_md = "\n".join(md_paginas.get(n, "") for n in (1, 2))
    def nombre_valido(v: str) -> bool:
        return (len(v) > 2 and not ETIQUETA.search(v) and not GENERICO.search(v) and not v.endswith(":")
                and "identificador" not in v.lower() and not v[0].islower() and not re.fullmatch(r"[\d\W]+", v))

    cab_crudo = "\n".join(crudo.get(n, "") for n in (1, 2))
    r = _buscar(CLAVES_PRODUCTO, cab_md, valido=nombre_valido) or _buscar(CLAVES_PRODUCTO, cab_crudo, valido=nombre_valido)
    if not r:
        r = _titulo_pagina1(md_paginas.get(1, ""), nombre_valido)
    if r:
        res["producto"], res["evidencia"]["producto"] = r[0], f"pág. 1-2 (md): {r[1]}"
    else:
        res["producto"] = ""
        notas.append("producto: no se encontró")

    # Código: md primero, luego texto crudo
    r = _buscar(CLAVES_CODIGO, cab_md) or _buscar(CLAVES_CODIGO, "\n".join(crudo.get(n, "") for n in (1, 2)))
    if r:
        res["codigo_producto"], res["evidencia"]["codigo_producto"] = r[0], r[1]
    else:
        res["codigo_producto"] = ""
        notas.append("codigo_producto: no aparece")

    # Versión y fecha: texto crudo (incluye encabezados/pies); respaldo, el Markdown completo
    for campo, claves in (("version", CLAVES_VERSION), ("fecha_revision", CLAVES_FECHA)):
        r = _buscar(claves, crudo_total)
        fuente = "texto crudo del PDF"
        if r:
            pag = pagina_de(crudo_total, r[1].split(" ")[0]) or ""
            fuente += f", pág. {pag}" if pag else ""
        else:
            r = _buscar(claves, md_total)
            fuente = "Markdown"
        if r:
            res[campo], res["evidencia"][campo] = r[0], f"{fuente}: {r[1]}"
        else:
            res[campo] = ""
            notas.append(f"{campo}: no aparece en el texto de la ficha")
    res["notas_metadatos"] = "; ".join(notas)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procesados", type=Path, default=Path("data/processed"))
    ap.add_argument("--raw", type=Path, default=Path("data/raw/FDS EVALUADAS"))
    ap.add_argument("--csv", type=Path, default=Path("verificacion/metadatos.csv"))
    args = ap.parse_args()

    pdfs = {p.name: p for p in args.raw.rglob("*.pdf")}
    filas = []
    for d in sorted(args.procesados.iterdir()):
        mp = d / "meta.json"
        if not mp.exists():
            continue
        meta = json.loads(mp.read_text(encoding="utf-8"))
        md = (d / "documento.md").read_text(encoding="utf-8")
        nuevo = extraer(_paginas_md(md), texto_crudo_pdf(pdfs[meta["archivo_original"]]))
        meta.update({k: nuevo[k] for k in ("fabricante", "producto", "codigo_producto", "version",
                                            "fecha_revision", "notas_metadatos")})
        meta["evidencia_metadatos"] = nuevo["evidencia"]
        m = re.search(r"versi(?:ó|o|#U00f3)n\s*(\d+)", meta["archivo_original"], flags=re.IGNORECASE)
        meta["version_en_nombre_archivo"] = m.group(1) if m else ""
        mp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        filas.append({"doc_id": meta["doc_id"], "anio": meta["anio_carpeta"], "fabricante": meta["fabricante"],
                      "producto": meta["producto"], "codigo_producto": meta["codigo_producto"],
                      "version": meta["version"], "fecha_revision": meta["fecha_revision"],
                      "version_en_nombre_archivo": meta["version_en_nombre_archivo"],
                      "notas": meta["notas_metadatos"], "revisado_por_autor": ""})
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    vacios = {c: sum(1 for f in filas if not f[c]) for c in
              ("fabricante", "producto", "codigo_producto", "version", "fecha_revision")}
    print(f"{len(filas)} fichas. Campos vacíos: {vacios}")


if __name__ == "__main__":
    main()
