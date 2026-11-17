"""Vuelca en verificacion/verificacion_extraccion.csv la verificación VISUAL del autor (muestra de 24 fichas) exportada por la página
verificacion/revision_muestra/index.html.

Qué se escribe, sin cambiar lo que el autor marcó, salvo un caso declarado:
  - verificado_por_autor : ok | con_errores (lo marcado por el autor);
  - errores_encontrados  : la nota del autor, tal cual;
  - observaciones        : contexto aportado por el asistente (revisión asistida por IA), SEPARADO de la decisión del autor.
Las 77 fichas restantes conservan su revisión automática y `verificado_por_autor` vacía.

Caso declarado: FDS 31. El autor marcó «ok» pero su nota dice «faltan codigos y numero en nafta» (describe el error); se registra `con_errores` por
coherencia con la nota y se deja constancia en `observaciones` para que el autor lo confirme.

Uso: python -m rag_fds.registrar_verificacion_autor verificacion/verificacion_extraccion_muestra_autor.json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

NOTAS_IA = {
    "fds010": "Verificada en la pág. 5 (tabla de EPP, rasterizada). La IA ve el contenido de protección corporal y de pies y la ducha de emergencia presentes, pero con los rótulos de los pictogramas mezclados en una fila («Proteccion obligatoria del cuerpo Proteccion obligatoria de pies … | los |») y texto basura de OCR («6RTo»); no ve filas ausentes.",
    "fds021": "El autor marcó «ok». La IA había señalado texto basura de OCR («6Bto») en una tabla de EPP de la pág. 4: discrepancia menor.",
    "fds027": "El autor marcó «ok». La IA había señalado texto basura de OCR («Alln») en una tabla de la pág. 7: discrepancia menor.",
    "fds031": "El autor marcó «ok» pero su nota describe el error (faltan códigos y número en la nafta); se registra con_errores por coherencia con la nota (pendiente de confirmar por el autor). La IA confirmó visualmente la pérdida de H350/H340/H313/H304 en la pág. 2.",
    "fds034": "El autor marcó «ok». La IA había señalado texto basura de OCR («6RTo») en una tabla de EPP de la pág. 5: discrepancia menor.",
    "fds042": "El autor marcó «ok». La IA había señalado texto basura de OCR («ORTO») en una tabla de EPP de la pág. 4: discrepancia menor.",
    "fds060": "El autor marcó «ok». La IA había señalado un ícono leído como ideograma (日) en la tabla de composición de la pág. 2: discrepancia.",
    "fds068": "Coincide con el hallazgo de la IA (ícono leído como ideograma, 回, junto a «<5 %»).",
    "fds070": "El autor marcó «ok». La IA había señalado un ícono leído como ideograma (风) y enlaces de imagen dentro de una celda en la pág. 2: discrepancia.",
    "fds075": "El autor marcó «ok». La IA había señalado «00» sin correspondencia y un ícono leído como ideograma (十) en la pág. 5: discrepancia.",
    "fds076": "Coincide con el hallazgo de la IA (ícono leído como ideograma, 日, junto a «<5 %»).",
    "fds089": "Coincide con el hallazgo de la IA (íconos leídos como ideogramas, 新 y 日).",
    "fds091": "Coincide con el hallazgo de la IA (ícono leído como ideograma, 新, como celda aislada).",
    "fds094": "Coincide con el hallazgo de la IA (íconos leídos como ideogramas, 日).",
    "fds007": "Muestra al azar; la revisión automática no halló diferencias.",
    "fds011": "Muestra al azar; el autor marcó errores sin describirlos. La IA ve en la tabla de composición de la pág. 1 las celdas combinadas duplicadas por Docling (columna «Nombre químico/clasificación» repetida); no ve diferencias de números. Pendiente: que el autor precise.",
    "fds015": "Muestra al azar. Esta ficha no tiene tablas en el Markdown (hallazgo 14 de errores_extraccion.md); el autor lo señala como «no hay markdown».",
    "fds023": "Muestra al azar; la revisión automática no halló diferencias.",
    "fds049": "Muestra al azar; la revisión automática no halló diferencias.",
    "fds054": "Muestra al azar; la revisión automática no halló diferencias.",
    "fds058": "Muestra al azar; la revisión automática no halló diferencias.",
    "fds081": "Muestra al azar; el autor marcó errores sin describirlos. La IA comparó la tabla de composición de la pág. 3 (5 ingredientes, CAS y concentraciones) con el PDF y coincide fila a fila; el error que vio el autor no se pudo identificar. Pendiente: que el autor precise.",
    "fds087": "Muestra al azar; el autor marcó errores sin describirlos. La IA comparó la tabla de composición de la pág. 3 (6 ingredientes, CAS y concentraciones) con el PDF y coincide fila a fila; el error que vio el autor no se pudo identificar. Pendiente: que el autor precise.",
    "fds099": "Muestra al azar; la revisión automática no halló diferencias.",
}


def main() -> None:
    entrada = Path(sys.argv[1])
    datos = json.loads(entrada.read_text(encoding="utf-8"))
    ruta = Path("verificacion/verificacion_extraccion.csv")
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
        campos = list(filas[0].keys())
    por_doc = {f["doc_id"]: f for f in filas}
    n_ok = n_err = 0
    for doc_id, d in datos.items():
        fila = por_doc[doc_id]
        decision = d["v"]
        if doc_id.startswith("fds031") and decision == "ok":
            decision = "con_errores"
        fila["verificado_por_autor"] = decision
        fila["errores_encontrados"] = d.get("e", "")
        fila["observaciones"] = NOTAS_IA[doc_id[:6]]
        n_ok += decision == "ok"
        n_err += decision == "con_errores"
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"{len(datos)} fichas registradas: {n_ok} coincide, {n_err} con errores. Fichas sin verificación humana: {len(filas) - len(datos)}")


if __name__ == "__main__":
    main()
