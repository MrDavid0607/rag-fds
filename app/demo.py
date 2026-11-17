"""Demo del RAG sobre FDS (Streamlit). Se ejecuta en local y solo escucha en 127.0.0.1.

    streamlit run app/demo.py --server.address 127.0.0.1 --server.port 8501

Requiere Ollama local (embeddings bge-m3 y generador) y el índice construido (python -m rag_fds.indice).
Muestra: respuesta, fuentes citadas (fabricante · producto · versión · documento · página · sección), fragmentos recuperados
en orden y las imágenes de las mismas páginas de los fragmentos citados.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import streamlit as st  # noqa: E402

from rag_fds.config import cargar  # noqa: E402
from rag_fds.indice import abrir_coleccion  # noqa: E402
from rag_fds.rag import cargar_catalogo, responder  # noqa: E402

st.set_page_config(page_title="RAG · Fichas de Datos de Seguridad", layout="wide")


@st.cache_resource(show_spinner="Abriendo el índice…")
def recursos(ruta_config: str):
    cfg = cargar(RAIZ / ruta_config)
    cfg["indice"]["ruta"] = str(RAIZ / cfg["indice"]["ruta"])
    cfg["corpus"]["procesados"] = str(RAIZ / cfg["corpus"]["procesados"])
    return cfg, abrir_coleccion(cfg), cargar_catalogo(cfg["corpus"]["procesados"])


st.title("Consulta de Fichas de Datos de Seguridad (FDS)")
st.caption("Pinturas y productos afines · 101 fichas · modelos locales con Ollama · cada afirmación lleva cita [n]")

with st.sidebar:
    st.header("Configuración")
    opcion = st.radio("Fragmentos recuperados (top-k)", ["config/topk6.yaml", "config/topk3.yaml"],
                      format_func=lambda x: "top-k = 6" if "6" in x else "top-k = 3")
    st.markdown("Todo lo demás (corpus, chunking, embeddings, generador, prompt) es idéntico entre las dos configuraciones.")
    ejemplos = [
        "¿Qué medios de extinción son adecuados para el Topcoat 400 1793 Blanco de International?",
        "¿Cuál es el teléfono de emergencia del proveedor del Sikafloor-2430 Part A?",
        "Compara la Pintura Primera Mano & Acabado de Corona entre la ficha de 2019 y la de 2021: tiempo máximo de almacenamiento y densidad a 20 ºC.",
        "¿Cuál es el rendimiento teórico en m² por galón del Acrolatex 50 3508 de Pintuco?",
        "¿Cuál es el punto de inflamación del producto Viniltex Advanced de Pintuco?",
    ]
    st.subheader("Ejemplos")
    for e in ejemplos:
        if st.button(e, use_container_width=True):
            st.session_state["pregunta"] = e

cfg, col, catalogo = recursos(opcion)
pregunta = st.text_area("Pregunta", key="pregunta", height=80, placeholder="Escribe tu pregunta sobre las FDS…")

if st.button("Consultar", type="primary") and pregunta.strip():
    with st.spinner("Recuperando fragmentos y generando la respuesta (puede tardar ~30 s)…"):
        r = responder(pregunta.strip(), cfg, col, catalogo)

    st.subheader("Respuesta")
    if r["evidencia_insuficiente"]:
        st.warning("El sistema indica que la evidencia en las FDS es insuficiente.")
    st.markdown(r["respuesta"])
    if r["citas_invalidas"]:
        st.error(f"La respuesta cita fragmentos que no existen: {r['citas_invalidas']}")
    if r["filtros"].get("variantes_sin_ficha"):
        st.info("Aviso: la pregunta menciona «" + "», «".join(r["filtros"]["variantes_sin_ficha"]) +
                "», que no corresponde exactamente a ninguna ficha del corpus.")

    st.subheader("Fuentes citadas")
    if r["fuentes"]:
        for f in r["fuentes"]:
            st.markdown(f"**[{f['n']}]** {f['fabricante']} · {f['producto']} · versión {f['version']} · "
                        f"`{f['documento']}` · pág. {f['pagina']} · sección {f['seccion']}")
    else:
        st.caption("La respuesta no cita ningún fragmento.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recuperación", f"{r['t_recuperacion_s']} s")
    c2.metric("Generación", f"{r['t_generacion_s']} s")
    c3.metric("Tokens/s", r["tokens_por_s"])
    c4.metric("Tokens del prompt", r["tokens_prompt"])

    with st.expander("Filtros aplicados a la búsqueda"):
        st.json(r["filtros"])

    st.subheader(f"Fragmentos recuperados (en orden, top-k = {r['top_k']})")
    citados = {f["n"] for f in r["fuentes"]}
    import json as _json
    for fr in r["fragmentos"]:
        m = fr["meta"]
        marca = " ✅ citado" if fr["n"] in citados else ""
        with st.expander(f"[{fr['n']}] {m['producto']} · pág. {m['pagina_inicio']}-{m['pagina_fin']} · "
                         f"sección {m['seccion_num']} {m['seccion_nombre']} · distancia {fr['distancia']:.3f}{marca}",
                         expanded=fr["n"] in citados):
            st.caption(f"{m['fabricante'] or 'fabricante no consta'} · versión {m['version'] or 'no consta'} · {m['archivo']}")
            st.text(fr["texto"].split("\n", 1)[-1])
            imgs = [RAIZ / p for p in _json.loads(m["imagenes"])]
            imgs = [p for p in imgs if p.exists()]
            if fr["n"] in citados and imgs:
                st.caption("Imágenes de las mismas páginas del documento (no se afirma que ilustren este texto):")
                st.image([str(p) for p in imgs[:6]], width=110)
