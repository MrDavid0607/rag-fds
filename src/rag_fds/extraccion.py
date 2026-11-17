"""Extracción PDF -> Markdown con Docling, conservando procedencia de página e imágenes técnicas.

Salida por ficha, en data/processed/<doc_id>/:
  documento.md   Markdown con marcas  <!-- pagina: N -->  antes del contenido de cada página.
  imagenes/      imágenes (pictogramas, tablas en imagen, etc.) enlazadas con rutas RELATIVAS.
  imagenes.json  por imagen: archivo, página, sección (último encabezado visto) y tamaño.
  meta.json      procedencia técnica: archivo original, carpeta/año, sha256, páginas, herramienta.

Los datos de contenido (fabricante, producto, versión, fecha) NO se infieren aquí: los extrae
metadatos.py del texto de la ficha y, si no aparecen, quedan vacíos con una nota.

Uso (desde la raíz del repo, con PYTHONPATH=src):
  python -m rag_fds.extraccion --entrada "data/raw/FDS EVALUADAS" --salida data/processed --numeros 5 31 47
  python -m rag_fds.extraccion --entrada "data/raw/FDS EVALUADAS" --salida data/processed          # todas
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from importlib import metadata
from pathlib import Path

# Imágenes menores a este lado (px, tras escalar) se consideran adornos/ruido y no se guardan.
MIN_LADO_PX = 40
ESCALA_IMAGENES = 2.0
PLACEHOLDER = "<!-- image -->"


# ------------------------------------------------------------------ utilidades de nombres
def decodificar_nombre(nombre: str) -> str:
    """Convierte escapes tipo '#U00ed' (=í) del nombre de archivo para mostrarlo. El original se conserva aparte."""
    return re.sub(r"#U([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), nombre)


def slug(texto: str, max_len: int = 60) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:max_len].strip("-")


def numero_fds(nombre: str) -> int | None:
    m = re.match(r"\s*FDS\s*(\d+)", decodificar_nombre(nombre), flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def construir_doc_id(nombre_pdf: str) -> str:
    """doc_id estable y legible: fds<NNN>-<resto-del-nombre>. El número FDS viene del nombre de archivo."""
    legible = decodificar_nombre(Path(nombre_pdf).stem)
    n = numero_fds(nombre_pdf)
    resto = re.sub(r"^\s*FDS\s*\d+\s*[-–_ ]*", "", legible, flags=re.IGNORECASE)
    return f"fds{n:03d}-{slug(resto)}" if n is not None else slug(legible)


def ram_pico_mb() -> int | None:
    """RAM pico del proceso en MB (Linux: resource; Windows: psutil). None si no se puede medir."""
    try:
        import resource  # solo Unix
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    except ImportError:
        try:
            import psutil
            return round(psutil.Process().memory_info().peak_wset / 2**20)
        except Exception:
            return None


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


# ------------------------------------------------------------------ conversor Docling
def crear_conversor():
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opciones = PdfPipelineOptions()
    opciones.do_table_structure = True        # estructura de tablas (celdas, filas, columnas)
    opciones.do_ocr = True                    # solo actúa donde hay imágenes con texto; los PDFs ya traen capa de texto
    opciones.generate_picture_images = True   # permite recortar cada imagen del PDF
    opciones.images_scale = ESCALA_IMAGENES
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opciones)})


def _seccion_por_pagina(doc) -> dict[int, list[tuple[str, str]]]:
    """Para cada imagen devuelve el último encabezado visto antes de ella en el orden de lectura."""
    from docling_core.types.doc import PictureItem, SectionHeaderItem, TitleItem

    ultimo = ""
    resultado: dict[int, list[tuple[str, str]]] = {}
    for item, _nivel in doc.iterate_items():
        if isinstance(item, (SectionHeaderItem, TitleItem)):
            ultimo = (item.text or "").strip()
        elif isinstance(item, PictureItem):
            pag = item.prov[0].page_no if item.prov else 0
            resultado.setdefault(pag, []).append((item.self_ref, ultimo))
    return resultado


def procesar_pdf(conversor, pdf: Path, salida: Path, carpeta_origen: str) -> dict:
    """Convierte un PDF y escribe documento.md, imagenes/, imagenes.json y meta.json. Devuelve métricas."""
    from docling_core.types.doc import PictureItem, TableItem

    doc_id = construir_doc_id(pdf.name)
    dir_doc = salida / doc_id
    dir_img = dir_doc / "imagenes"
    dir_img.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    resultado = conversor.convert(pdf)
    doc = resultado.document
    t_conv = time.perf_counter() - t0

    n_paginas = len(doc.pages)
    secciones = _seccion_por_pagina(doc)

    # Imágenes por página, en orden de lectura
    imagenes_por_pagina: dict[int, list[PictureItem]] = {}
    for pic in doc.pictures:
        pag = pic.prov[0].page_no if pic.prov else 0
        imagenes_por_pagina.setdefault(pag, []).append(pic)

    registro_imgs: list[dict] = []
    vistas: dict[str, str] = {}
    duplicadas: list[dict] = []
    omitidas = 0
    partes: list[str] = [f"<!-- doc_id: {doc_id} -->", f"<!-- archivo_original: {pdf.name} -->", ""]

    for pag in range(1, n_paginas + 1):
        md = doc.export_to_markdown(page_no=pag, image_placeholder=PLACEHOLDER)
        pics = imagenes_por_pagina.get(pag, [])
        sec_pag = {ref: s for ref, s in secciones.get(pag, [])}
        # Reemplaza cada marcador, en orden, por el enlace relativo a la imagen guardada (o lo quita si es ruido)
        trozos = md.split(PLACEHOLDER)
        reconstruido = trozos[0]
        for k, resto in enumerate(trozos[1:]):
            enlace = ""
            if k < len(pics):
                pic = pics[k]
                img = pic.get_image(doc)
                if img is not None and min(img.size) >= MIN_LADO_PX:
                    huella = hashlib.sha1(img.tobytes()).hexdigest()
                    if huella in vistas:
                        # Imagen idéntica a una ya guardada (típicamente el logo del encabezado en cada página):
                        # no se vuelve a guardar ni a enlazar, pero queda registrada para trazabilidad.
                        duplicadas.append({"pagina": pag, "duplicada_de": vistas[huella]})
                    else:
                        nombre = f"p{pag:03d}_img{k + 1:02d}.png"
                        img.save(dir_img / nombre)
                        vistas[huella] = f"imagenes/{nombre}"
                        bbox = pic.prov[0].bbox.as_tuple() if pic.prov else None
                        registro_imgs.append({
                            "archivo": f"imagenes/{nombre}",
                            "pagina": pag,
                            "seccion_aproximada": sec_pag.get(pic.self_ref, ""),
                            "bbox_pagina": list(bbox) if bbox else None,
                            "ancho_px": img.size[0],
                            "alto_px": img.size[1],
                            "relacion_con_tabla": None,  # solo se llena si hay evidencia explícita (no se infiere)
                        })
                        enlace = f"![imagen p{pag}](imagenes/{nombre})"
                else:
                    omitidas += 1
            reconstruido += enlace + resto
        partes.append(f"<!-- pagina: {pag} -->")
        partes.append(reconstruido.strip())
        partes.append("")

    (dir_doc / "documento.md").write_text("\n".join(partes), encoding="utf-8")
    (dir_doc / "imagenes.json").write_text(
        json.dumps({"imagenes": registro_imgs, "duplicadas_no_guardadas": duplicadas}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    n_tablas = sum(1 for it, _ in doc.iterate_items() if isinstance(it, TableItem))
    meta = {
        "doc_id": doc_id,
        "archivo_original": pdf.name,
        "nombre_mostrado": decodificar_nombre(pdf.name),
        "carpeta_origen": carpeta_origen,
        "anio_carpeta": (re.search(r"(20\d{2})", carpeta_origen) or [None, None])[1],
        "numero_fds": numero_fds(pdf.name),
        "sha256": sha256_archivo(pdf),
        "tamano_bytes": pdf.stat().st_size,
        "n_paginas": n_paginas,
        "n_tablas": n_tablas,
        "n_imagenes_guardadas": len(registro_imgs),
        "n_imagenes_omitidas_por_tamano": omitidas,
        "n_imagenes_duplicadas_no_guardadas": len(duplicadas),
        "herramienta_extraccion": {
            "docling": metadata.version("docling"),
            "docling_core": metadata.version("docling-core"),
            "ocr": "rapidocr " + metadata.version("rapidocr"),
        },
        # Rellenados por metadatos.py a partir del contenido; vacíos si no aparecen (nunca se infieren)
        "fabricante": "",
        "producto": "",
        "codigo_producto": "",
        "version": "",
        "fecha_revision": "",
        "notas_metadatos": "pendiente: lo llena metadatos.py",
    }
    (dir_doc / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "doc_id": doc_id,
        "n_paginas": n_paginas,
        "segundos_conversion": round(t_conv, 2),
        "segundos_por_pagina": round(t_conv / max(n_paginas, 1), 2),
        "n_tablas": n_tablas,
        "n_imagenes": len(registro_imgs),
    }


# ------------------------------------------------------------------ CLI
def main() -> None:
    ap = argparse.ArgumentParser(description="Extrae PDFs de FDS a Markdown con Docling.")
    ap.add_argument("--entrada", required=True, type=Path, help="Carpeta con subcarpetas por año (FDS 2018, ...).")
    ap.add_argument("--salida", required=True, type=Path, help="Carpeta de salida (data/processed).")
    ap.add_argument("--numeros", nargs="*", type=int, help="Solo estas fichas (número FDS del nombre).")
    ap.add_argument("--metricas", type=Path, default=Path("metricas/extraccion.json"))
    ap.add_argument("--forzar", action="store_true", help="Reprocesa aunque ya exista meta.json.")
    args = ap.parse_args()

    pdfs = sorted(args.entrada.rglob("*.pdf"), key=lambda p: (numero_fds(p.name) or 0, p.name))
    if args.numeros:
        pdfs = [p for p in pdfs if numero_fds(p.name) in set(args.numeros)]
    print(f"{len(pdfs)} PDFs a procesar")

    args.salida.mkdir(parents=True, exist_ok=True)
    conversor = crear_conversor()
    t_total = time.perf_counter()
    filas, errores = [], []
    for i, pdf in enumerate(pdfs, 1):
        doc_id = construir_doc_id(pdf.name)
        if (args.salida / doc_id / "meta.json").exists() and not args.forzar:
            print(f"[{i}/{len(pdfs)}] {doc_id}: ya existe, se omite")
            continue
        try:
            fila = procesar_pdf(conversor, pdf, args.salida, pdf.parent.name)
            filas.append(fila)
            print(f"[{i}/{len(pdfs)}] {doc_id}: {fila['n_paginas']} pág, {fila['segundos_conversion']} s, "
                  f"{fila['n_tablas']} tablas, {fila['n_imagenes']} imágenes", flush=True)
        except Exception as e:  # un fallo no detiene el lote: se registra como fallo de extracción
            errores.append({"doc_id": doc_id, "archivo": pdf.name, "error": f"{type(e).__name__}: {e}"})
            print(f"[{i}/{len(pdfs)}] {doc_id}: FALLO {type(e).__name__}: {e}", flush=True)

    total = time.perf_counter() - t_total
    paginas = sum(f["n_paginas"] for f in filas)
    resumen = {
        "fichas_ok": len(filas),
        "fichas_con_error": len(errores),
        "paginas": paginas,
        "segundos_total": round(total, 1),
        "segundos_por_pagina_promedio": round(total / max(paginas, 1), 2),
        "ram_pico_mb": ram_pico_mb(),
        "por_ficha": filas,
        "errores": errores,
    }
    args.metricas.parent.mkdir(parents=True, exist_ok=True)
    args.metricas.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in resumen.items() if k not in ("por_ficha",)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
