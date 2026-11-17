"""Página HTML para que el autor verifique las 12 preguntas y sus referencias contra el PDF.

Por pregunta muestra: el enunciado, la respuesta de referencia y, por cada evidencia, la página del PDF
(imagen) junto al fragmento que debe aparecer en ella. El autor marca "Verificada" o "Corregir" y exporta
sus respuestas (JSON) con el botón. NADA se marca como verificado automáticamente.

Uso: python -m rag_fds.revision_preguntas   ->  eval/revision_preguntas/index.html
"""
from __future__ import annotations

import html
import json
from pathlib import Path


def main() -> None:
    import pypdfium2 as pdfium

    datos = json.loads(Path("eval/preguntas.json").read_text(encoding="utf-8"))
    salida = Path("eval/revision_preguntas")
    (salida / "paginas").mkdir(parents=True, exist_ok=True)
    pdfs = {p.name: p for p in Path("data/raw/FDS EVALUADAS").rglob("*.pdf")}

    bloques = []
    for p in datos["preguntas"]:
        ev_html = []
        vistas = set()
        for e in p["evidencia"]:
            meta = json.loads(Path(f"data/processed/{e['doc_id']}/meta.json").read_text(encoding="utf-8"))
            clave = (e["doc_id"], e["pagina"])
            png = f"paginas/{e['doc_id']}_p{e['pagina']:03d}.png"
            if clave not in vistas:
                vistas.add(clave)
                if not (salida / png).exists():
                    pdfium.PdfDocument(str(pdfs[meta["archivo_original"]]))[e["pagina"] - 1].render(scale=1.4).to_pil().save(salida / png)
                ev_html.append(f'<div class="pag"><div class="et">{html.escape(e["documento"])} · página {e["pagina"]} · '
                               f'sección {html.escape(e["seccion"])}</div><img src="{png}" loading="lazy"></div>')
            ev_html.append(f'<div class="frag">Fragmento en p. {e["pagina"]} de {e["doc_id"][:6]}: <code>{html.escape(e["fragmento"])}</code></div>')
        ref = p.get("respuesta_referencia") or ("<i>Sin respuesta de referencia. Comportamiento esperado:</i> " +
                                                  html.escape(p.get("comportamiento_esperado", "")))
        ref = html.escape(ref) if p.get("respuesta_referencia") else ref
        notas = "".join(f'<p class="nota">{html.escape(p[k])}</p>' for k in ("nota_extraccion", "notas") if p.get(k))
        prods = "; ".join(f'{x["producto"]} ({x["fabricante"]}, {x["anio"]})' for x in p["productos"]) or "(ninguno en el corpus)"
        bloques.append(f"""<section class="q" data-id="{p['id']}"><h2>{p['id']} · {html.escape(p['tipo'])} · secciones {p['secciones']}</h2>
<p class="pregunta">{html.escape(p['pregunta'])}</p><p class="et">Productos: {html.escape(prods)}</p>
<div class="ref"><b>Respuesta de referencia (borrador):</b> {ref}</div>{notas}
<div class="evid">{''.join(ev_html)}</div>
<div class="form"><label><input type="radio" name="v_{p['id']}" value="verificada"> Verificada contra el PDF</label>
<label><input type="radio" name="v_{p['id']}" value="corregir"> Hay que corregir</label><br>
Observaciones / corrección: <textarea class="obs"></textarea></div></section>""")

    pagina = f"""<!doctype html><html lang="es"><meta charset="utf-8"><title>Verificación de las 12 preguntas</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;padding:1rem 2rem;background:#fafafa;color:#222}}
.q{{border-top:3px solid #888;margin:2rem 0;padding-top:.5rem}} .pregunta{{font-size:1.1rem;font-weight:600}}
.ref{{background:#e8f0fe;padding:.5rem .8rem;border-radius:4px}} .evid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:.6rem 0}}
.pag img{{width:100%;border:1px solid #ccc}} .et{{font-size:.78rem;color:#666}} .frag{{background:#fff;border:1px solid #ddd;padding:.4rem;font-size:.85rem;grid-column:span 2}}
.nota{{background:#fff4e5;padding:.4rem .6rem;font-size:.85rem}} .form{{background:#eef;padding:.5rem .8rem;border-radius:4px}} textarea{{width:95%;height:3em}}
nav{{position:sticky;top:0;background:#fafafa;padding:.4rem 0;border-bottom:1px solid #ccc}}</style>
<nav><b>Verificación de las 12 preguntas</b> · <button onclick="exportar()">Exportar mis respuestas (JSON)</button> <span id="est"></span></nav>
<p>Para cada pregunta compara la respuesta de referencia con la página del PDF y marca tu decisión. En las dos preguntas sin respuesta
confirma que el dato <b>no</b> está en el corpus. Nada de esto está marcado como verificado hasta que tú lo hagas.</p>
{''.join(bloques)}
<script>
const K='rev_preguntas'; let d={{}}; try{{d=JSON.parse(localStorage.getItem(K)||'{{}}')}}catch(e){{}}
function g(){{try{{localStorage.setItem(K,JSON.stringify(d))}}catch(e){{}} document.getElementById('est').textContent=' '+Object.values(d).filter(x=>x.v).length+' de 12 con decisión';}}
document.querySelectorAll('.q').forEach(s=>{{const id=s.dataset.id; const x=d[id]||(d[id]={{v:'',o:''}});
 s.querySelectorAll('input[type=radio]').forEach(r=>{{r.checked=r.value===x.v; r.onchange=()=>{{x.v=r.value;g()}}}});
 const o=s.querySelector('.obs'); o.value=x.o; o.oninput=()=>{{x.o=o.value;g()}};}}); g();
function exportar(){{const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{{type:'application/json'}})); a.download='verificacion_preguntas.json'; a.click();}}
</script></html>"""
    (salida / "index.html").write_text(pagina, encoding="utf-8")
    print(f"Escrito {salida / 'index.html'}")


if __name__ == "__main__":
    main()
