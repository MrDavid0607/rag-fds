"""Genera una página HTML de revisión: por página, la imagen del PDF a la izquierda y el Markdown extraído a la derecha.

Sirve para que el autor verifique visualmente la extracción (Fase 2: muestra; Fase 3: verificación de tablas).

Uso:
  python -m rag_fds.revision_html --procesados data/processed --raw "data/raw/FDS EVALUADAS" \
      --salida verificacion/muestra [--docs fds005-... fds031-...]
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


def paginas_markdown(texto: str) -> dict[int, str]:
    """Separa documento.md por las marcas <!-- pagina: N -->."""
    partes = re.split(r"<!-- pagina: (\d+) -->", texto)
    return {int(partes[i]): partes[i + 1].strip() for i in range(1, len(partes), 2)}


def renderizar_md(md: str, prefijo_img: str) -> str:
    from markdown_it import MarkdownIt

    cuerpo = MarkdownIt("commonmark").enable("table").render(md)
    return re.sub(r'src="imagenes/', f'src="{prefijo_img}/imagenes/', cuerpo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procesados", type=Path, default=Path("data/processed"))
    ap.add_argument("--raw", type=Path, default=Path("data/raw/FDS EVALUADAS"))
    ap.add_argument("--salida", type=Path, default=Path("verificacion/muestra"))
    ap.add_argument("--docs", nargs="*")
    args = ap.parse_args()

    import pypdfium2 as pdfium

    pdfs = {p.name: p for p in args.raw.rglob("*.pdf")}
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "paginas").mkdir(exist_ok=True)
    carpetas = sorted(d for d in args.procesados.iterdir() if (d / "meta.json").exists())
    if args.docs:
        carpetas = [d for d in carpetas if d.name in set(args.docs)]

    indice, bloques = [], []
    for d in carpetas:
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        pdf_ruta = pdfs[meta["archivo_original"]]
        pdf = pdfium.PdfDocument(str(pdf_ruta))
        paginas = paginas_markdown((d / "documento.md").read_text(encoding="utf-8"))
        # ruta relativa de los procesados vista desde la carpeta de salida
        rel = Path(__import__("os").path.relpath(d, args.salida)).as_posix()
        indice.append(f'<li><a href="#{d.name}">{html.escape(meta["nombre_mostrado"])}</a> '
                      f'({meta["n_paginas"]} pág., {meta["n_tablas"]} tablas)</li>')
        bloques.append(f'<h2 id="{d.name}">{html.escape(meta["nombre_mostrado"])}</h2>'
                       f'<p class="m">{d.name} · {meta["carpeta_origen"]} · sha256 {meta["sha256"][:12]}…</p>')
        for n in range(1, meta["n_paginas"] + 1):
            png = f"paginas/{d.name}_p{n:03d}.png"
            if not (args.salida / png).exists():
                pdf[n - 1].render(scale=1.4).to_pil().save(args.salida / png)
            md_html = renderizar_md(paginas.get(n, "*(sin contenido)*"), rel)
            bloques.append(
                f'<div class="par"><div class="izq"><div class="et">PDF · página {n}</div>'
                f'<img src="{png}" loading="lazy"></div>'
                f'<div class="der"><div class="et">Markdown · página {n}</div>{md_html}</div></div>')

    pagina = f"""<!doctype html><html lang="es"><meta charset="utf-8"><title>Revisión de extracción</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;padding:1rem 2rem;background:#fafafa;color:#222}}
.par{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:0 0 2rem;border-top:2px solid #bbb;padding-top:.5rem}}
.izq img{{width:100%;border:1px solid #ccc}} .et{{font-size:.75rem;color:#666;font-weight:600;margin-bottom:.3rem}}
.der{{background:#fff;border:1px solid #ddd;padding:.5rem 1rem;overflow:auto;max-height:1250px;font-size:.88rem}}
.der table{{border-collapse:collapse}} .der td,.der th{{border:1px solid #bbb;padding:2px 6px}}
.der img{{max-height:90px;border:1px dashed #aaa}} .m{{color:#666;font-size:.8rem}}
</style><h1>Revisión de la extracción</h1><ul>{''.join(indice)}</ul>{''.join(bloques)}</html>"""
    (args.salida / "index.html").write_text(pagina, encoding="utf-8")
    print(f"Escrito {args.salida / 'index.html'} con {len(carpetas)} fichas")


if __name__ == "__main__":
    main()
