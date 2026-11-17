"""Verificación de la extracción: una tabla con datos por ficha, pre-chequeo automático y páginas de revisión.

1. Elige en cada ficha una tabla con datos (prioridad: sección 3, 9, 8; si no hay, la de más números).
2. Pre-chequeo automático contra el texto crudo del PDF de esa página (pypdfium2):
   - cada número (con su unidad si la tiene) de la tabla del Markdown debe existir en el texto crudo;
   - los números del texto crudo de la página que NO están en el Markdown de esa página se reportan como perdidos.
3. Escribe verificacion/verificacion_extraccion.csv (la columna `verificado_por_autor` queda VACÍA: la llena el autor)
   y páginas HTML de revisión en tandas, con la imagen de la página del PDF junto a la tabla en Markdown.

El pre-chequeo NO sustituye la revisión humana; solo ayuda a priorizarla.

Uso: python -m rag_fds.verificacion --procesados data/processed --raw "data/raw/FDS EVALUADAS" --salida verificacion --tanda 20
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
from pathlib import Path

from rag_fds.secciones import ENCABEZADO, SECCIONES, clasificar, limpiar_linea, paginas_md, texto_crudo_pdf

PREFERENCIA = [3, 9, 8, 14, 2, 11, 15, 16]
UNIDAD = r"(%|[a-zA-Zµ°][a-zA-Zµ°/³²\.]*(?:/[a-zA-Z³²]+)?)"
NUM_UNIDAD = re.compile(rf"(?<![\w.])(\d+(?:[.,]\d+)*)\s*{UNIDAD}?")
# Palabras que siguen a un número y no son unidades (ruido): "2 de", "3 Tox"...
NO_UNIDAD = {"de", "a", "y", "o", "en", "el", "la", "los", "las", "por", "con", "del", "al", "se", "no", "es", "que", "tox", "cat"}


def normalizar(t: str) -> str:
    t = html.unescape(t.replace("\\_", "_")).lower()
    t = t.replace("³", "3").replace("²", "2").replace("µ", "u").replace("º", "°")
    return re.sub(r"\s+", " ", t)


def pares(texto: str) -> list[tuple[str, str]]:
    """Lista de (número, unidad) del texto; el número se normaliza (coma decimal -> punto)."""
    out = []
    for m in NUM_UNIDAD.finditer(normalizar(texto)):
        num = m.group(1).replace(",", ".")
        u = (m.group(2) or "").strip(".")
        if u in NO_UNIDAD or len(u) > 12:
            u = ""
        out.append((num, u))
    return out


def tablas_md(pagina: str) -> list[tuple[int, list[str]]]:
    """Bloques de tabla (líneas consecutivas que empiezan con '|') en una página. Devuelve (línea_inicial, líneas)."""
    lineas = pagina.splitlines()
    bloques, i = [], 0
    while i < len(lineas):
        if lineas[i].lstrip().startswith("|"):
            j = i
            while j < len(lineas) and lineas[j].lstrip().startswith("|"):
                j += 1
            if j - i >= 3 and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lineas[i + 1]):
                bloques.append((i, lineas[i:j]))
            i = j
        else:
            i += 1
    return bloques


def seccion_en_linea(pagina: str, n_linea: int, sec_inicial: int | None) -> int | None:
    """Sección vigente al llegar a la línea n_linea, siguiendo los encabezados anteriores de la página."""
    actual = sec_inicial
    for l in pagina.splitlines()[:n_linea]:
        for celda in (l.split("|") if "|" in l else [l]):
            c = limpiar_linea(celda)
            m = ENCABEZADO.match(c) if c else None
            if m and 1 <= int(m.group(1)) <= 16:
                n = clasificar(m.group("t"))
                if n:
                    actual = n
    return actual


def candidatas(paginas: dict[int, str]) -> list[dict]:
    res, sec = [], None
    for pag in sorted(paginas):
        for ini, lineas in tablas_md(paginas[pag]):
            sec_t = seccion_en_linea(paginas[pag], ini, sec)
            texto = "\n".join(lineas)
            datos = [p for p in pares(texto)]
            res.append({"pagina": pag, "seccion": sec_t, "lineas": lineas, "n_numeros": len(datos),
                        "filas": len(lineas) - 2})
        sec = seccion_en_linea(paginas[pag], len(paginas[pag].splitlines()), sec)
    return res


def elegir(cands: list[dict]) -> dict | None:
    utiles = [c for c in cands if c["n_numeros"] >= 3 and c["filas"] >= 2]
    for s in PREFERENCIA:
        for c in utiles:
            if c["seccion"] == s:
                return c
    if utiles:
        return max(utiles, key=lambda c: c["n_numeros"])
    return max(cands, key=lambda c: c["n_numeros"]) if cands else None


def prechequeo(tabla: dict, md_pagina: str, crudo_pagina: str) -> tuple[str, str]:
    crudo_n = normalizar(crudo_pagina)
    sin_espacios = re.sub(r"\s+", "", crudo_n)
    nums_crudo = {n for n, _ in pares(crudo_pagina)}
    faltan = []
    for num, uni in pares("\n".join(tabla["lineas"])):
        patron = re.escape(num.replace(".", "[.,]")).replace(r"\[\.,\]", "[.,]")
        patron = num.replace(".", "[.,]")
        if not re.search(rf"(?<![\d.,]){patron}(?![\d])", crudo_n):
            faltan.append(f"{num}{' ' + uni if uni else ''}")
        elif uni and not re.search(rf"{patron}\s*{re.escape(uni)}", crudo_n) \
                and re.sub(r"\s+", "", f"{num}{uni}") not in sin_espacios:
            faltan.append(f"{num} {uni} (unidad no coincide)")
    # Texto de las celdas (incluye unidades de las cabeceras, p. ej. "%" o "mg/m3"): debe existir en el texto crudo
    # (comparación sin espacios ni signos de guion de corte de línea)
    def compacto(x: str) -> str:
        return re.sub(r"[\s\-‐–]+", "", normalizar(x))

    crudo_compacto = compacto(crudo_pagina)
    for linea in tabla["lineas"]:
        if re.match(r"^\s*\|[\s:\-|]+\|\s*$", linea):
            continue
        for celda in linea.strip().strip("|").split("|"):
            c = re.sub(r"[*_`]", "", celda).strip()
            # 1) caracteres que no son del alfabeto latino/unidades (p. ej. un ícono leído por el OCR como "日")
            raros = re.findall(r"[^\x00-ɏͰ-Ͽ -⁯°%≥≤±µ²³‰′″´·–—−×]", c)  # latino + griego (µ, α...)
            if raros:
                faltan.append(f'carácter extraño {"".join(sorted(set(raros)))} en «{c[:30]}»')
            # 2) palabras de la celda que no existen en el texto crudo de la página (sin importar el orden)
            for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]{4,}", c):
                if compacto(w) not in crudo_compacto:
                    faltan.append(f'palabra «{w}»')
            # 3) unidades/símbolos sueltos (cabeceras como "%" o "mg/m3")
            if re.fullmatch(r"%|[a-zA-Zµ°]{1,3}/[a-zA-Z³²0-9]{1,3}", c) and compacto(c) not in crudo_compacto:
                faltan.append(f'unidad «{c}»')
    # Números perdidos: solo se miran las líneas del PDF que comparten algún número con la tabla (misma región);
    # así no se cuentan encabezados/pies de página ("Versión 1  Página 3/8") que Docling descarta a propósito.
    en_md = {n for n, _ in pares(md_pagina)}
    nums_tabla = {n for n, _ in pares("\n".join(tabla["lineas"]))}
    perdidos = set()
    for linea in crudo_pagina.splitlines():
        ln = normalizar(linea)
        if re.search(r"p[aá]gina\s*\d+\s*/\s*\d+|\b\d+\s*/\s*\d+\s*$|fecha|versi[oó]n|msds no", ln):
            continue
        ns = {n for n, _ in pares(ln)}
        if ns & nums_tabla:
            perdidos |= (ns - en_md)
    perdidos = sorted(perdidos, key=lambda x: (len(x), x))
    dif = []
    if faltan:
        dif.append("en la tabla pero no en el PDF: " + ", ".join(sorted(set(faltan))[:12]))
    if perdidos:
        dif.append(f"en líneas del PDF de esa tabla y no en el Markdown ({len(perdidos)}): " + ", ".join(perdidos[:12]))
    return ("OK" if not dif else "REVISAR"), " | ".join(dif)


PLANTILLA = """<!doctype html><html lang="es"><meta charset="utf-8"><title>Revisión {titulo}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;padding:1rem 2rem;background:#fafafa;color:#222}}
.ficha{{border-top:3px solid #888;margin:2rem 0;padding-top:.5rem}} .par{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
.par img{{width:100%;border:1px solid #ccc}} .md{{background:#fff;border:1px solid #ddd;padding:.5rem 1rem;overflow:auto;font-size:.85rem;max-height:1100px}}
.md table{{border-collapse:collapse}} .md td,.md th{{border:1px solid #bbb;padding:2px 6px}} .et{{font-size:.75rem;color:#666;font-weight:600}}
.auto{{padding:.4rem .6rem;border-radius:4px;margin:.4rem 0;font-size:.85rem}} .OK{{background:#e6f4ea}} .REVISAR{{background:#fff4e5}}
.form{{background:#eef;padding:.5rem .8rem;border-radius:4px;margin:.5rem 0}} .form textarea{{width:95%;height:3.2em}}
button{{padding:.4rem 1rem}} nav{{position:sticky;top:0;background:#fafafa;padding:.4rem 0;border-bottom:1px solid #ccc}}
</style><nav><b>{titulo}</b> · <button onclick="exportar()">Exportar mis respuestas (CSV)</button>
<span id="estado"></span> · <a href="index.html">índice</a></nav>
{cuerpo}
<script>
const CLAVE = 'rev_{tanda}';
let datos = {{}}; try {{ datos = JSON.parse(localStorage.getItem(CLAVE) || '{{}}'); }} catch (e) {{}}
function guardar() {{ try {{ localStorage.setItem(CLAVE, JSON.stringify(datos)); }} catch (e) {{}}
  const hechos = Object.values(datos).filter(d => d.v).length; document.getElementById('estado').textContent = ' ' + hechos + ' de {n} revisadas'; }}
document.querySelectorAll('.ficha').forEach(f => {{
  const id = f.dataset.doc; const d = datos[id] || (datos[id] = {{v:'', e:'', o:''}});
  f.querySelectorAll('input[type=radio]').forEach(r => {{ r.checked = (r.value === d.v); r.onchange = () => {{ d.v = r.value; guardar(); }}; }});
  const e = f.querySelector('.err'), o = f.querySelector('.obs'); e.value = d.e; o.value = d.o;
  e.oninput = () => {{ d.e = e.value; guardar(); }}; o.oninput = () => {{ d.o = o.value; guardar(); }};
}});
guardar();
function exportar() {{
  const filas = [['doc_id','verificado_por_autor','errores_encontrados','observaciones']];
  Object.entries(datos).forEach(([k, d]) => filas.push([k, d.v, d.e, d.o]));
  const csv = filas.map(r => r.map(c => '"' + String(c).replace(/"/g, '""') + '"').join(',')).join('\\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['\\ufeff' + csv], {{type: 'text/csv'}}));
  a.download = 'respuestas_{tanda}.csv'; a.click();
}}
</script></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procesados", type=Path, default=Path("data/processed"))
    ap.add_argument("--raw", type=Path, default=Path("data/raw/FDS EVALUADAS"))
    ap.add_argument("--salida", type=Path, default=Path("verificacion"))
    ap.add_argument("--tanda", type=int, default=20)
    args = ap.parse_args()

    import pypdfium2 as pdfium
    from markdown_it import MarkdownIt

    md_it = MarkdownIt("commonmark").enable("table")
    pdfs = {p.name: p for p in args.raw.rglob("*.pdf")}
    dir_rev = args.salida / "revision"
    (dir_rev / "paginas").mkdir(parents=True, exist_ok=True)

    filas_csv, bloques = [], []
    for d in sorted(args.procesados.iterdir()):
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        pm = paginas_md((d / "documento.md").read_text(encoding="utf-8"))
        crudo = texto_crudo_pdf(pdfs[meta["archivo_original"]])
        tabla = elegir(candidatas(pm))
        if tabla is None:
            filas_csv.append({"doc_id": meta["doc_id"], "pagina": "", "seccion": "", "elemento_revisado": "(sin tablas en el Markdown)",
                              "resultado_auto": "SIN_TABLA", "diferencias_auto": "", "verificado_por_autor": "",
                              "errores_encontrados": "", "observaciones": ""})
            bloques.append((meta, None, "SIN_TABLA", "", None))
            continue
        res, dif = prechequeo(tabla, pm[tabla["pagina"]], crudo[tabla["pagina"]])
        sec = tabla["seccion"]
        nombre_sec = f"{sec} {SECCIONES[sec][0]}" if sec else "(sin sección identificada)"
        elemento = f"tabla de {tabla['filas']} filas ({tabla['n_numeros']} valores numéricos)"
        filas_csv.append({"doc_id": meta["doc_id"], "pagina": tabla["pagina"], "seccion": nombre_sec,
                          "elemento_revisado": elemento, "resultado_auto": res, "diferencias_auto": dif,
                          "verificado_por_autor": "", "errores_encontrados": "", "observaciones": ""})
        bloques.append((meta, tabla, res, dif, nombre_sec))

    cols = list(filas_csv[0].keys())
    with open(args.salida / "verificacion_extraccion.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas_csv)

    # Páginas HTML en tandas
    indice = []
    for t, ini in enumerate(range(0, len(bloques), args.tanda), 1):
        grupo = bloques[ini:ini + args.tanda]
        cuerpo = []
        for meta, tabla, res, dif, nombre_sec in grupo:
            cab = (f'<h2>{html.escape(meta["nombre_mostrado"])}</h2><div class="et">{meta["doc_id"]} · {meta["carpeta_origen"]} · '
                   f'fabricante: {html.escape(meta["fabricante"] or "(no consta)")} · producto: {html.escape(meta["producto"])}</div>')
            if tabla is None:
                cuerpo.append(f'<div class="ficha" data-doc="{meta["doc_id"]}">{cab}<p>Esta ficha no tiene tablas en el Markdown. '
                              f'Revisa manualmente un bloque con datos (p. ej. sección 3 o 9).</p>{formulario()}</div>')
                continue
            png = f"paginas/{meta['doc_id']}_p{tabla['pagina']:03d}.png"
            if not (dir_rev / png).exists():
                pdf = pdfium.PdfDocument(str(pdfs[meta["archivo_original"]]))
                pdf[tabla["pagina"] - 1].render(scale=1.4).to_pil().save(dir_rev / png)
            tabla_html = md_it.render("\n".join(tabla["lineas"]))
            cuerpo.append(
                f'<div class="ficha" data-doc="{meta["doc_id"]}">{cab}'
                f'<div class="et">Sección {html.escape(nombre_sec)} · página {tabla["pagina"]}</div>'
                f'<div class="auto {res}"><b>Pre-chequeo automático: {res}</b> {html.escape(dif) or "(números y unidades de la tabla coinciden con el texto crudo)"}</div>'
                f'<div class="par"><div><div class="et">PDF · página {tabla["pagina"]}</div><img src="{png}" loading="lazy"></div>'
                f'<div><div class="et">Markdown extraído (tabla elegida)</div><div class="md">{tabla_html}</div></div></div>{formulario()}</div>')
        nombre = f"revision_{t:02d}.html"
        (dir_rev / nombre).write_text(PLANTILLA.format(titulo=f"tanda {t} (fichas {ini + 1}-{ini + len(grupo)})", cuerpo="".join(cuerpo),
                                                      tanda=f"{t:02d}", n=len(grupo)), encoding="utf-8")
        indice.append(f'<li><a href="{nombre}">Tanda {t}: fichas {ini + 1} a {ini + len(grupo)}</a></li>')
    (dir_rev / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Revisión</title><body style="font-family:system-ui;padding:2rem">'
        '<h1>Revisión de la extracción</h1><p>Compara cada tabla del PDF con el Markdown, marca el resultado y '
        'exporta tus respuestas (CSV) al terminar cada tanda.</p><ul>' + "".join(indice) + "</ul>", encoding="utf-8")

    from collections import Counter
    print(dict(Counter(f["resultado_auto"] for f in filas_csv)), f"{len(indice)} tandas")


def formulario() -> str:
    return ('<div class="form"><b>Tu verificación:</b> '
            '<label><input type="radio" name="v{0}" value="ok"> Coincide con el PDF</label> '
            '<label><input type="radio" name="v{0}" value="con_errores"> Tiene errores</label><br>'
            'Errores encontrados: <textarea class="err"></textarea> Observaciones: <textarea class="obs"></textarea></div>'
            ).replace("{0}", str(abs(hash(os.urandom(4)))))


if __name__ == "__main__":
    main()
