"""Revisión ASISTIDA POR IA de la extracción: comprueba TODAS las tablas del Markdown (no solo una por ficha) contra el texto crudo del PDF.

Para cada tabla: (a) cada número del Markdown debe existir en el texto crudo de la página; (b) cada palabra de las celdas debe existir en esa
página; (c) no debe haber caracteres que no sean del alfabeto latino/griego/unidades (íconos leídos como ideogramas). Es una comprobación
automática y NO sustituye la verificación visual del autor; la columna `verificado_por_autor` no se toca.

Salida: verificacion/revision_asistida_tablas.csv (una fila por tabla con hallazgos) y un resumen por ficha.
Uso: python -m rag_fds.revision_asistida_extraccion
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from rag_fds.secciones import paginas_md, texto_crudo_pdf
from rag_fds.verificacion import normalizar, pares, tablas_md


def compacto(x: str) -> str:
    return re.sub(r"[\s\-‐–]+", "", normalizar(x))


def revisar_tabla(lineas: list[str], crudo: str) -> list[str]:
    hallazgos = []
    nums_crudo = {n for n, _ in pares(crudo)}
    cc = compacto(crudo)
    nums_tabla = {n for n, _ in pares("\n".join(lineas)) if len(n) >= 2 or "." in n}
    faltan = sorted(n for n in nums_tabla if n not in nums_crudo)
    if faltan:
        hallazgos.append("números ausentes del PDF de la página: " + ", ".join(faltan[:8]))
    palabras_mal = []
    for linea in lineas:
        if re.match(r"^\s*\|[\s:\-|]+\|\s*$", linea):
            continue
        for celda in linea.strip().strip("|").split("|"):
            c = re.sub(r"[*_`]", "", celda).strip()
            raros = re.findall(r"[^\x00-\u024F\u0370-\u03FF\u2000-\u206F°%≥≤±µ²³‰′″´·–—−×]", c)
            if raros:
                hallazgos.append(f"carácter extraño {''.join(sorted(set(raros)))} en «{c[:30]}»")
            for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]{4,}", c):
                if compacto(w) not in cc:
                    palabras_mal.append(w)
    if palabras_mal:
        hallazgos.append("palabras ausentes del PDF de la página: " + ", ".join(sorted(set(palabras_mal))[:8]))
    return hallazgos


def main() -> None:
    pdfs = {p.name: p for p in Path("data/raw/FDS EVALUADAS").rglob("*.pdf")}
    filas, resumen = [], []
    for d in sorted(Path("data/processed").iterdir()):
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        pm = paginas_md((d / "documento.md").read_text(encoding="utf-8"))
        crudo = texto_crudo_pdf(pdfs[meta["archivo_original"]])
        n_tab = n_mal = 0
        for pag in sorted(pm):
            for ini, lineas in tablas_md(pm[pag]):
                n_tab += 1
                h = revisar_tabla(lineas, crudo.get(pag, ""))
                if h:
                    n_mal += 1
                    filas.append({"doc_id": meta["doc_id"], "pagina": pag, "filas_tabla": len(lineas) - 2, "hallazgos": " | ".join(h)})
        resumen.append((meta["doc_id"], n_tab, n_mal))
    with open("verificacion/revision_asistida_tablas.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id", "pagina", "filas_tabla", "hallazgos"])
        w.writeheader()
        w.writerows(filas)
    total_t, total_m = sum(r[1] for r in resumen), sum(r[2] for r in resumen)
    print(f"{len(resumen)} fichas · {total_t} tablas revisadas · {total_m} con algún hallazgo ({100 * total_m / max(total_t, 1):.1f} %)")
    print("fichas con hallazgos:", sum(1 for r in resumen if r[2]), "· fichas sin ninguno:", sum(1 for r in resumen if r[2] == 0))


if __name__ == "__main__":
    main()
