"""Comprobaciones automáticas del conjunto de evaluación (eval/preguntas.json). NO sustituyen la verificación humana.

1. Estructura: 12 preguntas = 6 directas + 4 integradoras/comparativas + 2 sin respuesta; al menos 4 secciones distintas;
   al menos una comparación de dos versiones del mismo producto.
2. Cada fragmento de evidencia existe LITERALMENTE (sin distinguir espacios, mayúsculas ni guiones de corte de línea) en el
   texto crudo del PDF de la página indicada y en el Markdown extraído.
3. Las preguntas no coinciden con las de desarrollo.
4. Las referencias no entran al índice: ni chunking.py ni indice.py ni rag.py leen eval/.

Uso: python -m rag_fds.validar_preguntas
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from rag_fds.secciones import paginas_md, texto_crudo_pdf


def compacto(t: str) -> str:
    t = t.replace("\\_", "_").replace("&amp;", "&").lower()
    return re.sub(r"[\s\-‐–|*]+", "", t)


def main() -> int:
    raiz = Path(".")
    datos = json.loads((raiz / "eval/preguntas.json").read_text(encoding="utf-8"))
    pregs = datos["preguntas"]
    dev = json.loads((raiz / "eval/preguntas_desarrollo.json").read_text(encoding="utf-8"))["preguntas"]
    errores: list[str] = []
    avisos: list[str] = []

    # 1. estructura
    tipos = [p["tipo"] for p in pregs]
    n_dir = tipos.count("directa")
    n_int = sum(1 for t in tipos if t.startswith(("integradora", "comparativa")))
    n_sin = tipos.count("sin_respuesta")
    secs = {s for p in pregs for s in p["secciones"]}
    if (len(pregs), n_dir, n_int, n_sin) != (12, 6, 4, 2):
        errores.append(f"estructura incorrecta: total={len(pregs)} directas={n_dir} integradoras={n_int} sin_respuesta={n_sin}")
    if len(secs) < 4:
        errores.append(f"solo cubre {len(secs)} secciones distintas")
    if "comparativa_versiones" not in tipos:
        errores.append("falta una comparación entre dos versiones del mismo producto")
    if len({p["id"] for p in pregs}) != len(pregs):
        errores.append("ids repetidos")

    # 2. evidencia literal en PDF y Markdown
    pdfs = {p.name: p for p in Path("data/raw/FDS EVALUADAS").rglob("*.pdf")}
    cache_crudo: dict[str, dict[int, str]] = {}
    cache_md: dict[str, dict[int, str]] = {}
    for p in pregs:
        if p["tipo"] != "sin_respuesta" and not p["evidencia"]:
            errores.append(f"{p['id']}: respondible sin evidencia")
        if p["tipo"] == "sin_respuesta" and p.get("respuesta_referencia"):
            errores.append(f"{p['id']}: una pregunta sin respuesta no debe tener respuesta de referencia")
        for e in p["evidencia"]:
            meta = json.loads((raiz / "data/processed" / e["doc_id"] / "meta.json").read_text(encoding="utf-8"))
            if e["doc_id"] not in cache_crudo:
                cache_crudo[e["doc_id"]] = texto_crudo_pdf(pdfs[meta["archivo_original"]])
                cache_md[e["doc_id"]] = paginas_md((raiz / "data/processed" / e["doc_id"] / "documento.md").read_text(encoding="utf-8"))
            frag = compacto(e["fragmento"])
            en_pdf = frag in compacto(cache_crudo[e["doc_id"]].get(e["pagina"], ""))
            en_md = frag in compacto(cache_md[e["doc_id"]].get(e["pagina"], ""))
            estado = ("PDF✓" if en_pdf else "PDF✗") + " " + ("MD✓" if en_md else "MD✗")
            print(f"  {p['id']} p{e['pagina']:>2} {estado}  {e['fragmento'][:70]}")
            if not en_pdf:
                errores.append(f"{p['id']}: fragmento no encontrado en el PDF (pág. {e['pagina']}): {e['fragmento'][:60]}")
            if not en_md:
                # Aviso, no error: en las FDS tipo formulario Docling separa la etiqueta de su valor; el dato sigue en el
                # Markdown pero no como frase literal. Debe constar en `nota_extraccion` de la pregunta.
                avisos.append(f"{p['id']}: «{e['fragmento'][:50]}» no está literal en el Markdown (pág. {e['pagina']})"
                              + ("" if p.get("nota_extraccion") else "  ← falta nota_extraccion"))
                if not p.get("nota_extraccion"):
                    errores.append(f"{p['id']}: fragmento no literal en el Markdown y sin nota_extraccion")
            if e["documento"] != meta["nombre_mostrado"]:
                errores.append(f"{p['id']}: nombre de documento distinto del de meta.json: {e['documento']}")

    # 3. distintas de desarrollo
    dev_txt = {re.sub(r"\W+", " ", q["pregunta"].lower()) for q in dev}
    for p in pregs:
        if re.sub(r"\W+", " ", p["pregunta"].lower()) in dev_txt:
            errores.append(f"{p['id']}: coincide con una pregunta de desarrollo")

    # 4. las referencias no se leen al indexar ni al generar
    for archivo in ("chunking.py", "indice.py", "rag.py"):
        codigo = (raiz / "src/rag_fds" / archivo).read_text(encoding="utf-8")
        if re.search(r"""["']eval[/\\"']|preguntas\.json|respuesta_referencia""", codigo):
            errores.append(f"{archivo} hace referencia a eval/ o a las respuestas de referencia")

    print(f"\nEstructura: {len(pregs)} preguntas ({n_dir} directas, {n_int} integradoras/comparativas, {n_sin} sin respuesta); "
          f"secciones cubiertas: {sorted(secs)}")
    print(f"Verificadas por el autor: {sum(1 for p in pregs if p.get('verificada'))} de {len(pregs)}")
    if avisos:
        print("\nAVISOS (dato presente en el Markdown pero con etiqueta y valor separados):")
        for a in avisos:
            print(" -", a)
    if errores:
        print("\nERRORES:")
        for e in errores:
            print(" -", e)
        return 1
    print("\nTodas las comprobaciones automáticas pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
