"""Prepara la revisión manual de la Fase 7: eval/revision_manual.md (plantilla con los datos ya reunidos) y
eval/revision_manual/index.html (PDF al lado de las citas, con formulario para el autor).

Casos: las 2 preguntas sin respuesta (e11, e12) y 3 respondibles, incluidos los de menor puntuación (e04, e07, e09).
TODO lo que dice "pre-chequeo" lo calcula el código; las conclusiones de exactitud y de correspondencia de las citas las
confirma el AUTOR mirando el PDF. Las casillas quedan vacías.

Uso: python -m rag_fds.revision_manual
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from rag_fds.verificacion import pares

SIN_RESPUESTA = ["e11", "e12"]
RESPONDIBLES = ["e04", "e07", "e09"]
CONFIGS = ["topk3", "topk6"]


def cargar() -> dict:
    preg = {p["id"]: p for p in json.loads(Path("eval/preguntas.json").read_text(encoding="utf-8"))["preguntas"]}
    resp = {k: {r["id"]: r for r in json.loads(Path(f"eval/respuestas_{k}.json").read_text(encoding="utf-8"))} for k in CONFIGS}
    res = {k: {r["id"]: r for r in json.loads(Path(f"eval/resultados_{k}.json").read_text(encoding="utf-8"))["resultados"]} for k in CONFIGS}
    diag = {}
    for k in CONFIGS:
        for i in RESPONDIBLES:
            f = Path(f"eval/diag_{k}_{i}.json")
            if f.exists():
                diag[(k, i)] = json.loads(f.read_text(encoding="utf-8"))
    return {"preg": preg, "resp": resp, "res": res, "diag": diag}


def trozos_con_cita(respuesta: str) -> list[tuple[str, list[int]]]:
    """Divide la respuesta en (texto, [citas]) por cada grupo de citas [n][m] que cierra una afirmación."""
    salida, pos = [], 0
    for m in re.finditer(r"((?:\[\d+(?:\s*[,;]\s*\d+)*\]\s*)+)", respuesta):
        texto = respuesta[pos:m.start()].strip()
        citas = [int(x) for x in re.findall(r"\d+", m.group(1))]
        salida.append((texto, citas))
        pos = m.end()
    return salida


def prechequeo_citas(respuesta: str, fragmentos: list[str]) -> list[dict]:
    """Para cada cita [n]: ¿los números (con unidad) de la afirmación aparecen en el fragmento n? Solo ayuda a priorizar."""
    filas = []
    for texto, citas in trozos_con_cita(respuesta):
        nums = [n for n, _ in pares(texto) if len(n) >= 2 or "." in n]
        for c in citas:
            if c < 1 or c > len(fragmentos):
                filas.append({"n": c, "afirmacion": texto, "resultado": "CITA INEXISTENTE", "faltan": []})
                continue
            frag = fragmentos[c - 1].replace(",", ".")
            faltan = [n for n in dict.fromkeys(nums) if not re.search(rf"(?<![\d.]){re.escape(n)}(?![\d])", frag)]
            res = "sin números en la afirmación" if not nums else ("los números aparecen en el fragmento" if not faltan else "FALTAN números en el fragmento")
            filas.append({"n": c, "afirmacion": texto, "resultado": res, "faltan": faltan})
    return filas


def etiqueta(m: dict) -> str:
    pag = m["pagina_inicio"] if m["pagina_inicio"] == m["pagina_fin"] else f"{m['pagina_inicio']}-{m['pagina_fin']}"
    return f"{m['doc_id']} · pág. {pag} · sección {m['seccion_num']}"


def resumen_f(v) -> str:
    return "NaN" if v is None else f"{v:.2f}"


def main() -> None:
    d = cargar()
    md = ["# Revisión manual (Fase 7)", "",
          "Plantilla preparada por el asistente. **Las casillas y conclusiones de exactitud las llena el autor** mirando los PDF; "
          "el asistente solo aporta datos y pre-chequeos automáticos. Versión web con el PDF al lado: `eval/revision_manual/index.html`.", "",
          "Casos: las 2 preguntas sin respuesta (e11, e12) y 3 respondibles con las puntuaciones más bajas o con fallos (e04, e07, e09). "
          "Otros casos con rechazos o respuestas incompletas (e08, e10) se comentan en `eval/analisis_resultados.md`.", ""]

    # ---------------- sin respuesta
    md += ["## A. Preguntas sin respuesta sustentada en el corpus", ""]
    for i in SIN_RESPUESTA:
        p = d["preg"][i]
        md += [f"### {i} — {p['pregunta']}", "", f"**Comportamiento esperado:** {p['comportamiento_esperado']}", ""]
        for k in CONFIGS:
            r = d["resp"][k][i]
            md += [f"**{k} (top-k {r['top_k']})** — el sistema {'SÍ dijo que no hay evidencia' if r['evidencia_insuficiente'] else 'NO dijo que no hay evidencia'}",
                   "", f"> {r['response'].replace(chr(10), ' ')}", "",
                   "Fragmentos recuperados: " + "; ".join(f"[{n}] {etiqueta(m)}" for n, m in enumerate(r["fragmentos_meta"], 1)), "",
                   f"- Fuentes que listó el sistema: {', '.join(r['fuentes']) if r['fuentes'] else '(ninguna)'}",
                   "- **Revisión del autor** — ¿reconoce la falta de evidencia o inventa?  ☐ reconoce  ☐ inventa  ☐ parcial", "- Observaciones: ", ""]

    # ---------------- respondibles
    md += ["## B. Casos respondibles (menor puntuación)", ""]
    for i in RESPONDIBLES:
        p = d["preg"][i]
        md += [f"### {i} — {p['tipo']} (secciones {p['secciones']})", "", f"**Pregunta:** {p['pregunta']}", "",
               f"**Referencia:** {p['respuesta_referencia']}", "", "Evidencia de la referencia:"]
        for e in p["evidencia"]:
            md.append(f"- {e['documento']} · pág. {e['pagina']} · sección {e['seccion']}: «{e['fragmento']}»")
        md += ["", "| Config | Faithfulness | Context Precision | Context Recall | Errores del evaluador |", "|---|---|---|---|---|"]
        for k in CONFIGS:
            r = d["res"][k][i]
            errs = "; ".join(f"{m}: {r['error_' + m]}" for m in ("faithfulness", "context_precision", "context_recall") if r.get("error_" + m)) or "—"
            md.append(f"| {k} | {resumen_f(r['faithfulness'])} | {resumen_f(r['context_precision'])} | {resumen_f(r['context_recall'])} | {errs} |")
        md.append("")
        for k in CONFIGS:
            r = d["resp"][k][i]
            md += [f"#### {k} (top-k {r['top_k']})", "", f"> {r['response'].replace(chr(10), ' ')}", "",
                   "Fragmentos recuperados, en orden: " + "; ".join(f"[{n}] {etiqueta(m)}" for n, m in enumerate(r["fragmentos_meta"], 1)), "",
                   "Pre-chequeo automático de cada cita (¿los números de la afirmación están en el fragmento citado?):", ""]
            for f in prechequeo_citas(r["response"], r["retrieved_contexts"]):
                faltan = f" ({', '.join(f['faltan'])})" if f["faltan"] else ""
                md.append(f"- [{f['n']}] «{f['afirmacion'][:110]}…» → {f['resultado']}{faltan}")
            dg = d["diag"].get((k, i))
            if dg:
                md += ["", "Pasos internos de Faithfulness (el evaluador genera las afirmaciones en inglés):", ""]
                md += [f"- [{v['verdict']}] {v['statement']} — {v['reason'][:220]}" for v in dg]
            md += ["", "- **Revisión del autor** — exactitud de la respuesta:  ☐ correcta  ☐ parcial  ☐ incorrecta",
                   "- Citas (cada [n] apunta a la página y sección correctas del PDF):  ☐ todas  ☐ algunas incorrectas  ☐ ninguna",
                   "- Observaciones: ", ""]

    Path("eval/revision_manual.md").write_text("\n".join(md), encoding="utf-8")

    # ---------------- HTML con el PDF al lado
    import pypdfium2 as pdfium

    pdfs = {p.name: p for p in Path("data/raw/FDS EVALUADAS").rglob("*.pdf")}
    sal = Path("eval/revision_manual")
    (sal / "paginas").mkdir(parents=True, exist_ok=True)

    def imagen(doc_id: str, pag: int) -> str:
        png = f"paginas/{doc_id}_p{pag:03d}.png"
        if not (sal / png).exists():
            meta = json.loads(Path(f"data/processed/{doc_id}/meta.json").read_text(encoding="utf-8"))
            pdfium.PdfDocument(str(pdfs[meta["archivo_original"]]))[pag - 1].render(scale=1.3).to_pil().save(sal / png)
        return png

    bloques = []
    for i in SIN_RESPUESTA + RESPONDIBLES:
        p = d["preg"][i]
        partes = [f'<h2>{i} · {html.escape(p["tipo"])}</h2><p class="q">{html.escape(p["pregunta"])}</p>']
        partes.append("<div class='ref'>" + (f"<b>Referencia:</b> {html.escape(p['respuesta_referencia'])}" if p.get("respuesta_referencia")
                                           else f"<b>Comportamiento esperado:</b> {html.escape(p['comportamiento_esperado'])}") + "</div>")
        for k in CONFIGS:
            r = d["resp"][k][i]
            citadas = sorted({c for _, cs in trozos_con_cita(r["response"]) for c in cs if 1 <= c <= len(r["fragmentos_meta"])})
            celdas = []
            for n in citadas:
                m = r["fragmentos_meta"][n - 1]
                celdas.append(f'<div class="cita"><div class="et">[{n}] {html.escape(etiqueta(m))}</div>'
                              f'<div class="frag">{html.escape(r["retrieved_contexts"][n - 1].split(chr(10), 1)[-1][:500])}…</div>'
                              f'<img loading="lazy" src="{imagen(m["doc_id"], m["pagina_inicio"])}"></div>')
            partes.append(f'<div class="cfg"><h3>{k}</h3><div class="resp">{html.escape(r["response"])}</div>'
                          f'<p class="et">Fragmentos recuperados: {", ".join(f"[{n}] {m["doc_id"][:14]} p{m["pagina_inicio"]}" for n, m in enumerate(r["fragmentos_meta"], 1))}</p>'
                          f'<div class="citas">{"".join(celdas) or "<i>(no cita ningún fragmento)</i>"}</div>'
                          f'<div class="form" data-k="{k}"><b>Tu revisión ({k}):</b> exactitud: '
                          f'<label><input type="radio" name="ex_{i}_{k}" value="correcta">correcta</label> '
                          f'<label><input type="radio" name="ex_{i}_{k}" value="parcial">parcial</label> '
                          f'<label><input type="radio" name="ex_{i}_{k}" value="incorrecta">incorrecta</label> · citas: '
                          f'<label><input type="radio" name="ci_{i}_{k}" value="todas_ok">todas correctas</label> '
                          f'<label><input type="radio" name="ci_{i}_{k}" value="alguna_mal">alguna incorrecta</label> '
                          f'<label><input type="radio" name="ci_{i}_{k}" value="ninguna_ok">ninguna</label><br>'
                          f'Observaciones: <textarea class="obs"></textarea></div></div>')
        bloques.append(f'<section class="caso" data-id="{i}">{"".join(partes)}</section>')

    pagina = f"""<!doctype html><html lang="es"><meta charset="utf-8"><title>Revisión manual (Fase 7)</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;padding:1rem 2rem;background:#fafafa;color:#222}}
.caso{{border-top:3px solid #888;margin:2rem 0;padding-top:.5rem}} .q{{font-weight:600;font-size:1.05rem}}
.ref{{background:#e8f0fe;padding:.5rem .8rem;border-radius:4px}} .cfg{{margin:1rem 0;padding:.5rem;border:1px solid #ccc;background:#fff}}
.resp{{background:#f6f6f6;padding:.5rem;white-space:pre-wrap}} .citas{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:.8rem;margin:.6rem 0}}
.cita img{{width:100%;border:1px solid #ccc}} .frag{{font-size:.8rem;background:#fffbe6;padding:.3rem;margin:.2rem 0}} .et{{font-size:.78rem;color:#555;font-weight:600}}
.form{{background:#eef;padding:.5rem .8rem;border-radius:4px}} textarea{{width:95%;height:3em}} nav{{position:sticky;top:0;background:#fafafa;padding:.4rem 0;border-bottom:1px solid #ccc}}</style>
<nav><b>Revisión manual</b> · <button onclick="exportar()">Exportar mis respuestas (JSON)</button> <span id="est"></span></nav>
<p>Compara cada respuesta con la página del PDF de cada fragmento citado: ¿el dato es exacto y la cita apunta a la página y sección correctas?
Las casillas están vacías: las decisiones son tuyas.</p>{''.join(bloques)}
<script>
const K='rev_manual'; let d={{}}; try{{d=JSON.parse(localStorage.getItem(K)||'{{}}')}}catch(e){{}}
function g(){{try{{localStorage.setItem(K,JSON.stringify(d))}}catch(e){{}}}}
document.querySelectorAll('.caso').forEach(s=>{{const id=s.dataset.id; s.querySelectorAll('.form').forEach(f=>{{const k=f.dataset.k; const key=id+'_'+k;
 const x=d[key]||(d[key]={{ex:'',ci:'',o:''}});
 f.querySelectorAll('input[type=radio]').forEach(r=>{{const campo=r.name.startsWith('ex_')?'ex':'ci'; r.checked=(x[campo]===r.value); r.onchange=()=>{{x[campo]=r.value;g()}}}});
 const o=f.querySelector('.obs'); o.value=x.o; o.oninput=()=>{{x.o=o.value;g()}};}})}});
function exportar(){{const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{{type:'application/json'}})); a.download='revision_manual_respuestas.json'; a.click();}}
</script></html>"""
    (sal / "index.html").write_text(pagina, encoding="utf-8")
    print("Escrito eval/revision_manual.md y eval/revision_manual/index.html")


if __name__ == "__main__":
    main()
