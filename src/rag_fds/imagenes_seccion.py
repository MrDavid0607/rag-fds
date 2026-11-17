"""Registra, para cada imagen de imagenes.json, la SECCIÓN de la FDS en la que aparece (número y nombre canónicos).

La guía pide registrar documento, página y sección de cada imagen. extraccion.py guardó el último encabezado visto ("seccion_aproximada");
aquí se calcula la sección canónica recorriendo el Markdown en orden de lectura: la sección vigente en el punto donde está el enlace a la imagen.
Una imagen antes del encabezado de la sección 1 (logos, pictogramas de portada) queda en la sección 0 «Encabezado del documento».
La imagen NO se asocia a una tabla: eso solo se haría con evidencia explícita, y `relacion_con_tabla` sigue en null.

Uso: python -m rag_fds.imagenes_seccion
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from rag_fds.chunking import seccion_de_linea
from rag_fds.secciones import SECCIONES

ENLACE = re.compile(r"!\[[^\]]*\]\((imagenes/[^)]+)\)")


def main() -> None:
    total = 0
    sin_seccion = 0
    for d in sorted(Path("data/processed").iterdir()):
        ruta = d / "imagenes.json"
        if not ruta.exists():
            continue
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        seccion, por_archivo = 0, {}
        for linea in (d / "documento.md").read_text(encoding="utf-8").splitlines():
            if linea.lstrip().startswith("!["):
                for ruta_img in ENLACE.findall(linea):
                    por_archivo[ruta_img] = seccion
                continue
            n = seccion_de_linea(linea)
            if n:
                seccion = n
        for img in datos["imagenes"]:
            n = por_archivo.get(img["archivo"], 0)
            img["seccion_num"] = n
            img["seccion_nombre"] = SECCIONES[n][0] if n in SECCIONES else "Encabezado del documento"
            total += 1
            sin_seccion += n == 0
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{total} imágenes con sección registrada ({sin_seccion} en el encabezado del documento, antes de la sección 1)")


if __name__ == "__main__":
    main()
