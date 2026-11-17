"""RAG sobre las FDS: recuperación con filtros por metadatos + generación con citas verificables.

Flujo:
  1. Se detectan en la pregunta fabricante, año y producto (por nombre) y se filtra el índice ANTES de buscar.
  2. Si la pregunta compara productos o versiones, se recupera POR producto/documento para que ninguno quede sin contexto
     (el total de fragmentos sigue siendo top_k).
  3. El generador recibe los fragmentos numerados [1..k] y debe citar [n] tras cada afirmación.
  4. La lista de fuentes (fabricante · producto · versión · documento · página · sección) la construye el CÓDIGO a partir de
     los metadatos de los fragmentos citados; el modelo no la escribe. Se marcan citas inexistentes.
  5. Si la evidencia no alcanza, el modelo debe decirlo ("No hay evidencia suficiente en las FDS disponibles para ...").

Uso:  python -m rag_fds.rag "pregunta" --config config/topk6.yaml [--json] [--solo-recuperar]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
import unicodedata
from pathlib import Path

import requests

from rag_fds.config import cargar
from rag_fds.indice import abrir_coleccion, embeber

# alias -> etiqueta canónica usada en el metadato `fabricante`
ALIAS_FABRICANTE = {
    "Pintuco": ["pintuco"], "Corona": ["corona", "corlanc"], "PPG": ["ppg"], "Pintuland": ["pintuland"],
    "INVESA": ["invesa", "sapolin"], "Sika": ["sika", "sikafloor"],
    "AkzoNobel": ["akzonobel", "akzo nobel", "aksonobel", "international"], "Bler": ["bler"],
}
GENERICAS = {"pintura", "esmalte", "base", "agua", "solvente", "parte", "part", "blanco", "negro", "gris", "acrilica",
             "acrilico", "epoxico", "epoxi", "resina", "resin", "componente", "premium", "superior", "color", "alta", "uso",
             "green", "powder", "series", "pinturas", "para", "mezcla", "linea", "trafico"}
# Temas que sugieren una sección de la FDS (palabras ya normalizadas, sin tildes). Solo SUMAN un pequeño bonus
# a los fragmentos de esa sección; no excluyen nada.
SECCION_TEMAS = {
    1: ["telefono de emergencia", "proveedor", "identificacion del producto", "uso recomendado", "datos del proveedor"],
    2: ["peligro", "pictograma", "palabra de advertencia", "clasificacion", "frases h", "indicaciones de peligro", "consejos de prudencia"],
    3: ["composicion", "ingrediente", "componente", "numero cas", " cas ", "porcentaje", "concentracion"],
    4: ["primeros auxilios", "contacto con los ojos", "inhalacion", "ingestion", "contacto con la piel"],
    5: ["incendio", "extincion", "extintor", "medios de extincion"],
    6: ["vertido", "derrame", "fuga", "limpieza de"],
    7: ["manipulacion", "almacenamiento", "almacenar", "manipular", "precauciones de manejo"],
    8: ["limite de exposicion", "proteccion personal", "epp", "guantes", "respirador", "proteccion respiratoria", "controles de exposicion", "tlv"],
    9: ["punto de inflamacion", "punto de ebullicion", "densidad", "viscosidad", "olor", "aspecto", "propiedades fisicas", "ph ", "solubilidad", "presion de vapor", "compuestos organicos volatiles", "cov"],
    10: ["estabilidad", "reactividad", "incompatible", "descomposicion peligrosa", "condiciones que deben evitarse"],
    11: ["toxicidad", "toxicologic", "dl50", "cl50", "carcinogen", "sensibilizacion", "mutagen"],
    12: ["ecologic", "ecotoxic", "biodegrad", "bioacumul", "toxicidad acuatica", "medio ambiente"],
    13: ["eliminacion", "residuo", "disposicion final", "desecho"],
    14: ["transporte", "numero onu", "clase de peligro para el transporte", "adr", "imdg", "iata"],
    15: ["reglamentaria", "normativa", "legislacion", "decreto"],
    16: ["otra informacion", "fecha de revision", "referencias bibliograficas", "abreviaturas"],
}
PALABRAS_COMPARACION = ("compar", "diferenc", "versus", " vs ", "frente a", "respecto a", "mas o menos", "distint",
                        "cambi", "actualiz", "versiones", "ambos", "ambas", "mayor", "menor", "cual de")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ------------------------------------------------------------------ catálogo y filtros
def cargar_catalogo(raiz: str | Path) -> list[dict]:
    docs = []
    for d in sorted(Path(raiz).iterdir()):
        mp = d / "meta.json"
        if mp.exists():
            m = json.loads(mp.read_text(encoding="utf-8"))
            docs.append({"doc_id": m["doc_id"], "producto": m["producto"], "fabricante": m.get("fabricante") or "",
                         "anio": str(m.get("anio_carpeta") or ""), "producto_norm": norm(m["producto"])})
    return docs


def detectar_filtros(pregunta: str, catalogo: list[dict]) -> dict:
    q = " " + norm(pregunta) + " "
    qtok = set(q.split())
    fabricantes = [f for f, al in ALIAS_FABRICANTE.items() if any(f" {norm(a)} " in q for a in al)]
    anios = sorted(set(re.findall(r"\b(20(?:1[89]|2[0-5]))\b", pregunta)))

    # tokens "raros" del nombre del producto (aparecen en pocos documentos) que la pregunta menciona
    from collections import Counter
    df = Counter(t for d in catalogo for t in set(d["producto_norm"].split()))
    def raros(d):
        return {t for t in d["producto_norm"].split() if len(t) >= 4 and t not in GENERICAS and df[t] <= 8}
    mencionados = {t for d in catalogo for t in raros(d) if t in qtok}
    docs = [d for d in catalogo if raros(d) & mencionados]
    comparacion = any(p in q for p in PALABRAS_COMPARACION)
    # Si la pregunta trae códigos numéricos, gana el documento que coincide en más (p. ej. "1793" distingue
    # TOPCOAT 400 1793 de TOPCOAT 400 1772). En una comparación entre productos se conserva la unión.
    numeros = {t for t in qtok if t.isdigit() and len(t) >= 3 and t not in anios}
    if docs and numeros and not comparacion:
        puntaje = {d["doc_id"]: len(numeros & set(d["producto_norm"].split())) for d in docs}
        mejor = max(puntaje.values())
        if mejor > 0:
            docs = [d for d in docs if puntaje[d["doc_id"]] == mejor]
    # Sin comparación, el producto mejor emparejado (más tokens raros del nombre en la pregunta) gana
    if docs and not comparacion:
        cuenta = {d["doc_id"]: len(raros(d) & qtok) for d in docs}
        mejor = max(cuenta.values())
        docs = [d for d in docs if cuenta[d["doc_id"]] == mejor]
    return {"fabricantes": fabricantes, "anios": anios, "docs_producto": docs, "comparacion": comparacion,
            "secciones": secciones_de_pregunta(q), "variantes_sin_ficha": variantes_sin_ficha(pregunta, mencionados, docs)}


# Palabras que pueden seguir al nombre de un producto sin ser parte de él
_STOP_SIG = {"de", "del", "la", "el", "los", "las", "en", "con", "para", "por", "que", "como", "cual", "cuales", "segun", "entre",
             "frente", "versus", "respecto", "ficha", "fichas", "fds", "producto", "version", "versiones", "ano", "anio", "hay",
             "tiene", "tienen", "indica", "dice", "dicen", "recomienda", "cuando", "donde", "cuanto", "cuantos", "sobre", "si",
             "esta", "estan", "contiene", "usa", "usar", "debe", "deben", "punto", "porcentaje", "valor", "tipo", "clase", "numero",
             "medios", "primeros", "medidas", "precauciones", "proveedor", "telefono", "fabricante"}


def variantes_sin_ficha(pregunta: str, mencionados: set[str], docs: list[dict]) -> list[str]:
    """Palabra que sigue al nombre del producto en la pregunta y NO figura en el nombre de la ficha encontrada
    (p. ej. "Viniltex Advanced" cuando solo existe "VINILTEX PRO 650 BLANCO"): señal de que se pregunta por otro producto."""
    if not docs or not mencionados:
        return []
    toks = norm(pregunta).split()
    en_fichas = {t for d in docs for t in d["producto_norm"].split()}
    alias = {norm(a) for al in ALIAS_FABRICANTE.values() for a in al}
    sospechosas = []
    for i, t in enumerate(toks[:-1]):
        if t in mencionados:
            sig = toks[i + 1]
            if len(sig) >= 4 and sig.isalpha() and sig not in _STOP_SIG and sig not in en_fichas and sig not in alias \
                    and sig not in GENERICAS and not any(sig in tema for temas in SECCION_TEMAS.values() for tema in temas):
                sospechosas.append(f"{t} {sig}")
    return sospechosas


def secciones_de_pregunta(q_norm: str) -> list[int]:
    return [n for n, temas in SECCION_TEMAS.items() if any(t in q_norm for t in temas)]


def construir_where(doc_ids: list[str] | None, fabricantes: list[str], anios: list[str],
                    secciones: list[int] | None = None) -> dict | None:
    cond = []
    if doc_ids:
        cond.append({"doc_id": {"$in": doc_ids}})
    if fabricantes:
        cond.append({"fabricante": {"$in": fabricantes}})
    if anios:
        cond.append({"anio": {"$in": anios}})
    if secciones:
        cond.append({"seccion_num": {"$in": secciones}})
    if not cond:
        return None
    return cond[0] if len(cond) == 1 else {"$and": cond}


# ------------------------------------------------------------------ recuperación
def recuperar(pregunta: str, cfg: dict, col, catalogo: list[dict], top_k: int | None = None) -> dict:
    k = top_k or cfg["top_k"]
    t0 = time.perf_counter()
    vec = embeber([pregunta], cfg["embeddings"])[0]
    t_emb = time.perf_counter() - t0

    f = detectar_filtros(pregunta, catalogo) if cfg["recuperacion"]["aplicar_filtros_metadatos"] else \
        {"fabricantes": [], "anios": [], "docs_producto": [], "comparacion": False, "secciones": [], "variantes_sin_ficha": []}
    bonus = cfg["recuperacion"].get("bonus_seccion", 0.0)
    docs = f["docs_producto"]
    notas = []
    # restricciones de fabricante/año sobre los documentos de producto detectados
    if docs and f["fabricantes"]:
        sub = [d for d in docs if d["fabricante"] in f["fabricantes"]]
        docs = sub or docs
        if not sub:
            notas.append("el fabricante nombrado no coincide con el producto; se ignora el fabricante")
    if docs and f["anios"]:
        sub = [d for d in docs if d["anio"] in f["anios"]]
        docs = sub or docs
        if not sub:
            notas.append("el año nombrado no coincide con los documentos del producto; se ignora el año")

    n_cand = cfg["recuperacion"]["candidatos_por_grupo"]
    # grupos de recuperación
    if f["comparacion"] and len(docs) >= 2:
        por_producto = len({d["producto_norm"] for d in docs}) > 1
        claves = {}
        for d in docs:
            claves.setdefault(d["producto_norm"] if por_producto else d["doc_id"], []).append(d["doc_id"])
        grupos = list(claves.values())
    elif docs:
        grupos = [[d["doc_id"] for d in docs]]
    else:
        grupos = [None]

    resultados = []
    t1 = time.perf_counter()
    for gi, g in enumerate(grupos):
        fab, anios = ([], []) if docs else (f["fabricantes"], f["anios"])
        vistos: dict[str, dict] = {}
        consultas = [construir_where(g, fab, anios)]
        if f["secciones"] and bonus:
            consultas.append(construir_where(g, fab, anios, f["secciones"]))   # candidatos extra de la sección probable
        for where in consultas:
            r = col.query(query_embeddings=[vec], n_results=n_cand, where=where)
            for i in range(len(r["ids"][0])):
                vistos[r["ids"][0][i]] = {"id": r["ids"][0][i], "texto": r["documents"][0][i], "meta": r["metadatas"][0][i],
                                          "distancia": r["distances"][0][i], "grupo": gi}
        for v in vistos.values():
            v["ajustada"] = v["distancia"] - (bonus if v["meta"]["seccion_num"] in f["secciones"] else 0.0)
            resultados.append(v)
    t_busq = time.perf_counter() - t1

    # reparto de los k lugares entre grupos (en comparaciones); en un solo grupo es el top-k directo
    por_grupo: dict[int, list[dict]] = {}
    for r in sorted(resultados, key=lambda x: x["ajustada"]):
        por_grupo.setdefault(r["grupo"], []).append(r)
    orden_grupos = sorted(por_grupo, key=lambda g: por_grupo[g][0]["ajustada"])[:k]
    cupo = {g: k // len(orden_grupos) + (1 if i < k % len(orden_grupos) else 0) for i, g in enumerate(orden_grupos)} if orden_grupos else {}
    elegidos = []
    for g in orden_grupos:
        elegidos.extend(por_grupo[g][:cupo[g]])
    # si algún grupo tuvo menos candidatos que su cupo, se completa con los mejores restantes
    if len(elegidos) < k:
        ya = {e["id"] for e in elegidos}
        sobran = [r for r in sorted(resultados, key=lambda x: x["ajustada"]) if r["id"] not in ya]
        elegidos.extend(sobran[:k - len(elegidos)])
    elegidos.sort(key=lambda x: x["ajustada"])
    for n, e in enumerate(elegidos, 1):
        e["n"] = n
    return {"fragmentos": elegidos,
            "filtros": {"fabricantes": f["fabricantes"], "anios": f["anios"], "secciones_probables": f["secciones"],
                        "productos": sorted({d["producto"] for d in docs}), "docs": [d["doc_id"] for d in docs],
                        "comparacion": f["comparacion"], "grupos": len(grupos), "notas": notas,
                        "variantes_sin_ficha": f.get("variantes_sin_ficha", [])},
            "t_embedding_s": round(t_emb, 3), "t_busqueda_s": round(t_busq, 3), "t_recuperacion_s": round(t_emb + t_busq, 3)}


# ------------------------------------------------------------------ generación
def etiqueta_fuente(m: dict) -> str:
    pag = m["pagina_inicio"] if m["pagina_inicio"] == m["pagina_fin"] else f"{m['pagina_inicio']}-{m['pagina_fin']}"
    return (f"fabricante: {m['fabricante'] or 'no consta en la ficha'} | producto: {m['producto']} | "
            f"versión: {m['version'] or 'no consta'} | documento: {m['archivo']} | páginas: {pag} | "
            f"sección: {m['seccion_num']} {m['seccion_nombre']}")


def armar_contexto(fragmentos: list[dict]) -> str:
    bloques = []
    for f in fragmentos:
        cuerpo = f["texto"].split("\n", 1)[1] if f["texto"].startswith("[") and "\n" in f["texto"] else f["texto"]
        bloques.append(f"[{f['n']}] ({etiqueta_fuente(f['meta'])})\n{cuerpo}")
    return "\n\n".join(bloques)


def aviso_producto(filtros: dict, fragmentos: list[dict]) -> str:
    """Aviso determinista para el generador cuando la pregunta parece nombrar una variante que no tiene ficha."""
    var = filtros.get("variantes_sin_ficha") or []
    if not var:
        return ""
    existentes = sorted({f["meta"]["producto"] for f in fragmentos})
    return (f"AVISO DEL SISTEMA: la pregunta menciona «{'», «'.join(var)}», pero los fragmentos solo corresponden a "
            f"{', '.join(existentes)}. Si «{var[0]}» no es el mismo producto que aparece en los fragmentos, no uses esos datos como "
            f"si fueran de ese producto: responde con «No hay evidencia suficiente en las FDS disponibles para ...» e indica qué producto sí aparece.\n")


def generar(pregunta: str, fragmentos: list[dict], cfg: dict, filtros: dict | None = None) -> dict:
    g = cfg["generador"]
    aviso = aviso_producto(filtros or {}, fragmentos)
    mensajes = [
        {"role": "system", "content": cfg["prompt"]["sistema"].strip()},
        {"role": "user", "content": cfg["prompt"]["usuario"].format(pregunta=pregunta, aviso=aviso, contexto=armar_contexto(fragmentos)).strip()},
    ]
    r = requests.post(g["ollama_url"].rstrip("/") + "/api/chat", timeout=g["timeout_s"], json={
        "model": g["modelo"], "messages": mensajes, "stream": False, "keep_alive": g["keep_alive"],
        "options": {"temperature": g["temperature"], "seed": g["seed"], "num_ctx": g["num_ctx"], "num_predict": g["num_predict"]},
    })
    r.raise_for_status()
    d = r.json()
    ns = 1e9
    return {
        "respuesta": d["message"]["content"].strip(),
        "t_generacion_s": round(d["total_duration"] / ns, 2),
        "t_carga_modelo_s": round(d.get("load_duration", 0) / ns, 2),
        "tokens_prompt": d.get("prompt_eval_count"), "tokens_generados": d.get("eval_count"),
        "tokens_por_s": round(d["eval_count"] / (d["eval_duration"] / ns), 2) if d.get("eval_duration") else None,
    }


def citas_usadas(respuesta: str) -> list[int]:
    usados = []
    for grupo in re.findall(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]", respuesta):
        usados += [int(x) for x in re.findall(r"\d+", grupo)]
    return sorted(set(usados))


def fuentes(respuesta: str, fragmentos: list[dict]) -> dict:
    por_n = {f["n"]: f for f in fragmentos}
    usadas = citas_usadas(respuesta)
    lista = []
    for n in usadas:
        if n in por_n:
            m = por_n[n]["meta"]
            pag = m["pagina_inicio"] if m["pagina_inicio"] == m["pagina_fin"] else f"{m['pagina_inicio']}-{m['pagina_fin']}"
            lista.append({"n": n, "fabricante": m["fabricante"] or "no consta en la ficha", "producto": m["producto"],
                          "version": m["version"] or "no consta", "documento": m["archivo"], "pagina": pag,
                          "seccion": f"{m['seccion_num']} {m['seccion_nombre']}"})
    return {"fuentes": lista, "citas_invalidas": [n for n in usadas if n not in por_n]}


def responder(pregunta: str, cfg: dict, col=None, catalogo: list[dict] | None = None, generar_respuesta: bool = True) -> dict:
    col = col or abrir_coleccion(cfg)
    catalogo = catalogo or cargar_catalogo(cfg["corpus"]["procesados"])
    rec = recuperar(pregunta, cfg, col, catalogo)
    salida = {"pregunta": pregunta, "top_k": cfg["top_k"], **rec}
    if generar_respuesta:
        gen = generar(pregunta, rec["fragmentos"], cfg, rec["filtros"])
        salida.update(gen)
        salida.update(fuentes(gen["respuesta"], rec["fragmentos"]))
        salida["evidencia_insuficiente"] = gen["respuesta"].lstrip().lower().startswith(cfg["mensaje_sin_evidencia"].lower())
        salida["tiempo_total_s"] = round(rec["t_recuperacion_s"] + gen["t_generacion_s"], 2)
    return salida


def formato_texto(r: dict) -> str:
    out = [f"PREGUNTA: {r['pregunta']}  (top_k={r['top_k']})", f"Filtros: {json.dumps(r['filtros'], ensure_ascii=False)}", ""]
    if "respuesta" in r:
        out += ["RESPUESTA:", r["respuesta"], ""]
        out.append("FUENTES:")
        for f in r["fuentes"]:
            out.append(f"  [{f['n']}] {f['fabricante']} · {f['producto']} · versión {f['version']} · {f['documento']} · "
                       f"pág. {f['pagina']} · sección {f['seccion']}")
        if r["citas_invalidas"]:
            out.append(f"  ¡ATENCIÓN! Citas a fragmentos inexistentes: {r['citas_invalidas']}")
        if not r["fuentes"] and not r["evidencia_insuficiente"]:
            out.append("  (la respuesta no cita ningún fragmento)")
        out.append("")
        out.append(f"Tiempos: recuperación {r['t_recuperacion_s']} s · generación {r['t_generacion_s']} s · "
                   f"{r['tokens_por_s']} tokens/s · prompt {r['tokens_prompt']} tok")
    out += ["", "FRAGMENTOS RECUPERADOS (en orden):"]
    for f in r["fragmentos"]:
        m = f["meta"]
        out.append(f"  [{f['n']}] dist={f['distancia']:.3f} {m['producto']} | pág {m['pagina_inicio']}-{m['pagina_fin']} | "
                   f"sec {m['seccion_num']} | {f['texto'].split(chr(10), 1)[-1][:110].strip()}…")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pregunta")
    ap.add_argument("--config", default="config/topk6.yaml")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--solo-recuperar", action="store_true")
    args = ap.parse_args()
    cfg = cargar(args.config)
    r = responder(args.pregunta, cfg, generar_respuesta=not args.solo_recuperar)
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else formato_texto(r))


if __name__ == "__main__":
    main()
