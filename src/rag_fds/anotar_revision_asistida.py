"""Añade a verificacion/verificacion_extraccion.csv las columnas `revision_asistida_ia` y `notas_revision_asistida`.

IMPORTANTE: es una revisión ASISTIDA POR IA (Claude): comprobación automática de TODAS las tablas de cada ficha contra el texto crudo del PDF
(`revision_asistida_extraccion.py`) más inspección visual de unas pocas páginas (FDS 31 págs. 2 y 5, FDS 35 pág. 1). NO es la verificación del autor:
la columna `verificado_por_autor` no se toca y sigue vacía.

Clasificación de los 37 hallazgos automáticos (1 248 tablas revisadas):
  - falsos positivos (17): enlaces a imágenes dentro de celdas, subíndice CO₂, símbolo ˚, texto de logo (AkzoNobel), etiqueta «FLAMMABLE LIQUID»;
  - ruido de OCR en textos de imágenes (6): «6RTo», «6Bto», «ORTO», «Alln», «00»;
  - íconos leídos como ideogramas (8 tablas, 8 fichas): 日 回 风 十 新;
  - FDS 31 (6): PDF parcialmente rasterizado; la tabla de composición de la pág. 2 perdió los códigos de peligro de una fila (verificado visualmente).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

# prefijo de ficha -> nota (hallazgos REALES comprobados; las demás fichas con solo falsos positivos se anotan como sin hallazgos relevantes)
REALES = {
    "fds010": "Pág. 5: la tabla de EPP contiene texto basura de OCR («6RTo») procedente de una imagen.",
    "fds021": "Pág. 4: texto basura de OCR («6Bto») en una tabla de EPP.",
    "fds027": "Pág. 7: texto basura de OCR («Alln») en una tabla.",
    "fds034": "Pág. 5: texto basura de OCR («6RTo») en una tabla de EPP.",
    "fds042": "Pág. 4: texto basura de OCR («ORTO») en una tabla de EPP.",
    "fds060": "Pág. 2: un ícono leído como ideograma (日) en la tabla de composición.",
    "fds068": "Pág. 2: un ícono leído como ideograma (回) junto a «<5 %».",
    "fds070": "Pág. 2: un ícono leído como ideograma (风) en una celda, con enlaces de imagen dentro de la tabla.",
    "fds075": "Pág. 5: «00» sin correspondencia en el PDF y un ícono leído como ideograma (十) junto a «Lavaojos».",
    "fds076": "Pág. 2: un ícono leído como ideograma (日) junto a «<5 %».",
    "fds089": "Pág. 2: íconos leídos como ideogramas (新, 日) en la tabla de composición.",
    "fds091": "Pág. 2: un ícono leído como ideograma (新) como celda aislada.",
    "fds094": "Pág. 2: íconos leídos como ideogramas (日) en 3 celdas de la tabla de composición.",
    "fds031": "PDF parcialmente rasterizado (tablas como imagen, texto por OCR). Pág. 2, tabla de composición: la fila de «Nafta (petróleo), fracción pesada» "
              "perdió sus códigos de peligro (en el PDF: Carc. 1B: H350; Muta. 1B: H340; Tox. Agud. 5: H313; Tox. Asp. 1: H304 - Peligro; en el Markdown: «Car. - H : M. : : Mgro»). "
              "Verificado visualmente. La tabla de EPP de la pág. 5 se comprobó visualmente y coincide con el PDF.",
}


def main() -> None:
    ruta = Path("verificacion/verificacion_extraccion.csv")
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    campos = [c for c in filas[0].keys() if c not in ("revision_asistida_ia", "notas_revision_asistida")]
    campos += ["revision_asistida_ia", "notas_revision_asistida"]
    for fila in filas:
        pre = fila["doc_id"][:6]
        if pre in REALES:
            fila["revision_asistida_ia"] = "HALLAZGO"
            fila["notas_revision_asistida"] = REALES[pre]
        else:
            fila["revision_asistida_ia"] = "sin hallazgos relevantes"
            fila["notas_revision_asistida"] = "Todas las tablas de la ficha comprobadas automáticamente contra el texto crudo del PDF (revisión asistida por IA; no es verificación del autor)."
        if not re.match(r"^$|^(ok|con_errores)$", fila.get("verificado_por_autor", "")):
            raise SystemExit("verificado_por_autor tiene contenido inesperado; no se modifica")
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    n_h = sum(1 for f in filas if f["revision_asistida_ia"] == "HALLAZGO")
    print(f"{len(filas)} fichas: {n_h} con hallazgos reales, {len(filas) - n_h} sin hallazgos relevantes; verificado_por_autor intacta")


if __name__ == "__main__":
    main()
