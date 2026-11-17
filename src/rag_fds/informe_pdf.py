"""Convierte informe/informe.md a PDF (Edge/Chrome sin cabeza) y verifica que no pase de 2 páginas.

Uso: python -m rag_fds.informe_pdf
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CSS = """@page{size:A4;margin:11mm 12mm}
body{font-family:'Segoe UI',Arial,sans-serif;font-size:9.6pt;line-height:1.33;color:#111}
h1{font-size:14pt;margin:0 0 2px}h2{font-size:11pt;margin:8px 0 2px;border-bottom:1px solid #bbb}
p,ul{margin:2px 0}li{margin:0}table{border-collapse:collapse;width:100%;margin:3px 0;font-size:8pt}
th,td{border:1px solid #999;padding:1.5px 4px;text-align:left}th{background:#eee}"""


def main() -> int:
    from markdown_it import MarkdownIt

    md = Path("informe/informe.md").read_text(encoding="utf-8")
    cuerpo = MarkdownIt("commonmark").enable("table").render(md)
    ruta_html = Path("informe/informe.html")
    ruta_html.write_text(f'<!doctype html><html lang="es"><meta charset="utf-8"><title>Informe</title><style>{CSS}</style><body>{cuerpo}</body></html>',
                         encoding="utf-8")
    navegadores = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    exe = next((n for n in navegadores if Path(n).exists()), None)
    if not exe:
        print("No se encontró Edge ni Chrome")
        return 1
    pdf = Path("informe/informe.pdf").resolve()
    subprocess.run([exe, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", ruta_html.resolve().as_uri()],
                   check=True, capture_output=True, timeout=120)
    import pypdfium2 as pdfium

    n = len(pdfium.PdfDocument(str(pdf)))
    print(f"informe.pdf: {n} página(s)")
    ruta_html.unlink()
    return 0 if n <= 2 else 2


if __name__ == "__main__":
    sys.exit(main())
