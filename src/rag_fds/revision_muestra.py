"""Página de verificación HUMANA acotada (≈ 15 minutos): las 14 fichas con hallazgos reales de la revisión asistida por IA + 10 fichas al azar.

Método mixto, declarado como tal: el 100 % de las tablas de las 101 fichas se comprobó automáticamente contra el texto del PDF
(`revision_asistida_extraccion.py`) y el autor verifica visualmente esta muestra de 24 fichas. La página NO rellena nada por el autor:
las marcas las hace él y se exportan en un JSON.

Uso: python -m rag_fds.revision_muestra   ->  verificacion/revision_muestra/index.html
"""
from __future__ import annotations

import csv
import html
import json
import random
from pathlib import Path

from rag_fds.anotar_revision_asistida import REALES
from rag_fds.secciones import paginas_md
from rag_fds.verificacion import tablas_md

SEMILLA = 7
N_AZAR = 10


def main() -> None:
    import pypdfium2 as pdfium
    from markdown_it import MarkdownIt

    md_it = MarkdownIt("commonmark").enable("table")
    pdfs = {p.name: p for p in Path("data/raw/FDS EVALUADAS").rglob("*.pdf")}
    sal = Path("verificacion/revision_muestra")
    (sal / "paginas").mkdir(parents=True, exist_ok=True)

    asistida = list(csv.DictReader(open("verificacion/revision_asistida_tablas.csv", encoding="utf-8-sig")))
    elegidas = {f["doc_id"]: f for f in csv.DictReader(open("verificacion/verificacion_extraccion.csv", encoding="utf-8-sig"))}
    docs = sorted(elegidas)
    con_hallazgo = [d for d in docs if d[:6] in REALES]
    resto = [d for d in docs if d[:6] not in REALES]
    azar = sorted(random.Random(SEMILLA).sample(resto, N_AZAR))
    # SIN_TABLA (FDS 2, 15, 16, 17) no se puede verificar con una tabla: ya están entre las fichas a mirar si salen al azar
    seleccion = [(d, "hallazgo") for d in con_hallazgo] + [(d, "azar") for d in azar]

    bloques = []
    for d, motivo in seleccion:
        meta = json.loads(Path(f"data/processed/{d}/meta.json").read_text(encoding="utf-8"))
        pm = paginas_md((Path("data/processed") / d / "documento.md").read_text(encoding="utf-8"))
        if motivo == "hallazgo":
            paginas = sorted({int(r["pagina"]) for r in asistida if r["doc_id"] == d})[:2]
            nota = f'<div class="ia"><b>Lo que encontró la revisión asistida por IA:</b> {html.escape(REALES[d[:6]])}</div>'
        else:
            e = elegidas[d]
            paginas = [int(e["pagina"])] if e["pagina"] else [1]
            nota = '<div class="ia">Ficha elegida <b>al azar</b> (la revisión automática no encontró nada). Comprueba que los números y unidades de la tabla coincidan con el PDF.</div>'
        partes = [f'<section class="ficha" data-doc="{d}"><h2>{html.escape(meta["nombre_mostrado"])}</h2>'
                  f'<div class="et">{d} · {meta["carpeta_origen"]} · motivo: {"hallazgo de la IA" if motivo == "hallazgo" else "muestra al azar"}</div>{nota}']
        pdf = pdfium.PdfDocument(str(pdfs[meta["archivo_original"]]))
        for pag in paginas:
            png = f"paginas/{d}_p{pag:03d}.png"
            if not (sal / png).exists():
                pdf[pag - 1].render(scale=1.4).to_pil().save(sal / png)
            tablas = [md_it.render("\n".join(lineas)) for _, lineas in tablas_md(pm.get(pag, ""))] or ["<i>(sin tablas en el Markdown de esta página)</i>"]
            partes.append(f'<div class="par"><div><div class="et">PDF · página {pag}</div><img loading="lazy" src="{png}"></div>'
                          f'<div><div class="et">Tablas del Markdown en la página {pag}</div><div class="md">{"<hr>".join(tablas)}</div></div></div>')
        partes.append('<div class="form"><b>Tu verificación:</b> '
                      f'<label><input type="radio" name="v_{d}" value="ok"> Coincide con el PDF</label> '
                      f'<label><input type="radio" name="v_{d}" value="con_errores"> Tiene errores</label><br>'
                      'Errores encontrados: <textarea class="err"></textarea></div></section>')
        bloques.append("".join(partes))

    pagina = f"""<!doctype html><html lang="es"><meta charset="utf-8"><title>Verificación de la extracción (muestra)</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;padding:1rem 2rem;background:#fafafa;color:#222}}
.ficha{{border-top:3px solid #888;margin:2rem 0;padding-top:.5rem}} .par{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:.5rem 0}}
.par img{{width:100%;border:1px solid #ccc}} .md{{background:#fff;border:1px solid #ddd;padding:.5rem 1rem;overflow:auto;max-height:1150px;font-size:.84rem}}
.md table{{border-collapse:collapse}} .md td,.md th{{border:1px solid #bbb;padding:2px 6px}} .et{{font-size:.75rem;color:#666;font-weight:600}}
.ia{{background:#fff4e5;padding:.4rem .6rem;border-radius:4px;font-size:.85rem;margin:.3rem 0}} .form{{background:#eef;padding:.5rem .8rem;border-radius:4px}}
textarea{{width:95%;height:3em}} nav{{position:sticky;top:0;background:#fafafa;padding:.4rem 0;border-bottom:1px solid #ccc}}</style>
<nav><b>Verificación de la extracción: {len(seleccion)} fichas</b> · <button onclick="exportar()">Exportar mis respuestas (JSON)</button> <span id="est"></span></nav>
<p>Para cada ficha compara la <b>página del PDF</b> (izquierda) con las <b>tablas en Markdown</b> (derecha): números, unidades y nombres. Marca tu decisión; las casillas empiezan vacías y las decisiones son tuyas.</p>
{''.join(bloques)}
<script>
const K='rev_muestra'; let d={{}}; try{{d=JSON.parse(localStorage.getItem(K)||'{{}}')}}catch(e){{}}
function g(){{try{{localStorage.setItem(K,JSON.stringify(d))}}catch(e){{}} document.getElementById('est').textContent=' '+Object.values(d).filter(x=>x.v).length+' de {len(seleccion)} con decisión';}}
document.querySelectorAll('.ficha').forEach(s=>{{const id=s.dataset.doc; const x=d[id]||(d[id]={{v:'',e:''}});
 s.querySelectorAll('input[type=radio]').forEach(r=>{{r.checked=r.value===x.v; r.onchange=()=>{{x.v=r.value;g()}}}});
 const e=s.querySelector('.err'); e.value=x.e; e.oninput=()=>{{x.e=e.value;g()}};}}); g();
function exportar(){{const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{{type:'application/json'}})); a.download='verificacion_extraccion_muestra.json'; a.click();}}
</script></html>"""
    (sal / "index.html").write_text(pagina, encoding="utf-8")
    print(f"Escrito {sal / 'index.html'} con {len(seleccion)} fichas ({len(con_hallazgo)} con hallazgo, {len(azar)} al azar: {', '.join(a[:6] for a in azar)})")


if __name__ == "__main__":
    main()
