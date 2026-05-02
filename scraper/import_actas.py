"""
Acta Civium — importación de actas PDF a Supabase.
Usa httpx + REST API (sin supabase-py).

Uso:
  cd actacivium/scraper
  python import_actas.py
"""
import re
import sys
import time
from pathlib import Path

import httpx
import pdfplumber
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/").removesuffix("/rest/v1")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ACTAS_DIR    = Path(__file__).parent.parent.parent / "actas_muestra"

if not SUPABASE_URL or SUPABASE_URL == "https://xxxxxxxxxxxx.supabase.co":
    print("Rellena SUPABASE_URL y SUPABASE_KEY en el archivo .env")
    sys.exit(1)

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation",
}


# ── REST helpers ──────────────────────────────────────────────────────────────

def sb_get(table: str, params: dict = {}) -> list:
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def sb_post(table: str, data: dict) -> dict:
    r = httpx.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, json=data, timeout=15)
    r.raise_for_status()
    result = r.json()
    return result[0] if isinstance(result, list) else result

def sb_patch(table: str, filters: dict, data: dict):
    params = {k: f"eq.{v}" for k, v in filters.items()}
    r = httpx.patch(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS,
                    params=params, json=data, timeout=15)
    r.raise_for_status()

def sb_delete(table: str, filters: dict):
    params = {k: f"eq.{v}" for k, v in filters.items()}
    r = httpx.delete(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS,
                     params=params, timeout=15)
    r.raise_for_status()


# ── Extracción de texto ───────────────────────────────────────────────────────

def extraer_texto(pdf_path: Path) -> str:
    partes = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text(x_tolerance=2, y_tolerance=2)
            if t:
                partes.append(t)
    texto = "\n".join(partes)
    texto = re.sub(r"AKTA \d+ ACTA \d+\n[^\n]+\n", "", texto)
    texto = re.sub(r"\n{4,}", "\n\n\n", texto)
    return texto.strip()


def extraer_meta(texto: str, nombre_archivo: str) -> dict:
    meta = {}

    m = re.search(r"acta_(\d+)_(\d{4})(\d{2})(\d{2})", nombre_archivo)
    if m:
        meta["numero_acta"] = int(m.group(1))
        meta["fecha"] = f"{m.group(2)}-{m.group(3)}-{m.group(4)}"

    m = re.search(r"SESI[ÓO]N:\s*(Ordinaria|Extraordinaria|Urgente)", texto, re.I)
    meta["tipo_sesion"] = m.group(1).lower() if m else "ordinaria"

    m = re.search(r"HORA DE COMIENZO:\s*(\d{1,2}:\d{2})", texto)
    meta["hora_inicio"] = m.group(1) if m else None

    m = re.search(r"PRESIDE:\s*Don(?:a|ña)?\s+([^\n,]+)", texto)
    meta["alcalde_nombre"] = m.group(1).strip() if m else None

    m = re.search(r"SECRETARIA?:\s*Do[ñn]a?\s+([^\n,]+)", texto)
    meta["secretaria_nombre"] = m.group(1).strip() if m else None

    # Asistencia: buscar lista de concejales en cabecera
    cabecera = texto[:4000]
    asistentes = re.findall(r"Don(?:a|ña)?\s+[A-Z][^\n]{5,40}", cabecera)
    ausentes_m = re.findall(r"NO ASISTE[NS]?:(.+?)SECRETARIA", texto, re.DOTALL)
    meta["n_asistentes"] = len(asistentes)
    meta["n_ausentes"]   = len(re.findall(r"Don(?:a|ña)?", ausentes_m[0])) if ausentes_m else 0

    return meta


# ── Constantes de clasificación ───────────────────────────────────────────────

_SPANISH = (
    r"(?:Aprobaci|Dar\s+cuenta|Toma\s+de|Declaraci|Proposici|Moci[oó]n|Tratamiento|"
    r"Modificaci|Informaci|Debate|Ratificaci|Acuerdo|Adjudicaci|Contrataci|"
    r"Subvenci|Ordenanza|Presupuest|Plan\s|Convenio|Concesi|Daci|Resoluci|"
    r"Nombramiento|Autorizaci|Desestimaci|Licencia|Estudio\s+de|Exped)"
)

# Comisión → categoría
COMISION_CAT_MAP = [
    (["DESARROLLO", "PLANIFICACI", "TERRITORIO", "URBAN"], "urbanismo"),
    (["HACIENDA", "PRESUPUEST", "TESORER", "PATRIMONI", "CEMENTERI"], "hacienda"),
    (["SERVICIOS A LAS PERSONAS", "BIENESTAR", "SOCIAL", "SANIDAD",
      "EDUCACI", "DEPENDENCI", "VULNERAB"], "servicios_sociales"),
    (["MOVILIDAD", "TRANSPORTE", "TRÁFICO", "APARCAM", "BICICLETA"], "movilidad"),
    (["CULTURA", "MUSEO", "FESTIVAL", "DEPORTE"], "cultura"),
    (["MEDIO AMBIENTE", "RESIDUOS", "CLIMA", "SOSTENIB", "BIORESIDU"], "medio_ambiente"),
    (["DERECHOS", "IGUALDAD", "GÉNERO", "MUJER", "LGTBI", "VIOLENCIA"], "derechos"),
    (["SEGURIDAD", "POLICÍA", "BOMBERO"], "seguridad"),
]

CATS = {
    "vivienda":           ["vivienda","etxebizitza","alquiler","tasada","habitacional","renta"],
    "urbanismo":          ["urbanismo","plan general","pgou","ordenación","parcela",
                           "estudio de detalle","plan especial","licencia de obra",
                           "convenio urbanístico","uso del suelo","expediente urbanístico"],
    "hacienda":           ["ordenanza fiscal","impuesto","tasa","presupuesto","ibo","icio","iae",
                           "modificación presupuestaria","cuenta general","tributo","exacción",
                           "cementerio","prestación patrimonial"],
    "medio_ambiente":     ["medio ambiente","residuos","bioresiduo","reciclaje","emisiones",
                           "clima","sostenib","contaminaci","parque natural","arbolado"],
    "servicios_sociales": ["servicios sociales","bienestar","ayuda","dependencia",
                           "exclusión","vulnerabl","emergencia social","atención primaria"],
    "movilidad":          ["movilidad","transporte","tráfico","ota","aparcamiento","bus",
                           "bicicleta","carril bici","peatonal","zona azul","taxi"],
    "cultura":            ["cultura","festival","museo","deporte","educación","biblioteca",
                           "teatro","música","patrimonio cultural"],
    "derechos":           ["derechos","igualdad","género","violencia","lgtbi",
                           "discriminación","mujer","feminismo","diversidad"],
    "gobernanza":         ["delegación","compatibilidad","nombramiento","cese",
                           "concejal","alcalde","organización municipal","reglamento orgánico",
                           "junta de gobierno","moción de censura"],
    "seguridad":          ["seguridad","policía","bombero","emergencias","protección civil"],
}

TIPOS = {
    "aprobacion_definitiva":     ["aprobación definitiva","behin-betiko"],
    "aprobacion_inicial":        ["aprobación inicial","hasierako onarpen"],
    "dar_cuenta":                ["dar cuenta","berri ematea","toma de conocimiento"],
    "proposicion_normativa":     ["proposición normativa","arau proposamena"],
    "mocion":                    ["moción ordinaria","moción de control","moción urgente"],
    "declaracion_institucional": ["declaración institucional","erakunde adierazpen"],
    "interpelacion":             ["interpelación"],
    "pregunta_oral":             ["pregunta oral"],
}

# Comisión → campo comision (schema)
COMISION_SCHEMA = {
    "urbanismo":          "territorio",
    "hacienda":           "hacienda",
    "servicios_sociales": "servicios_personas",
    "movilidad":          "territorio",
    "cultura":            "servicios_personas",
    "medio_ambiente":     "servicios_personas",
    "derechos":           "servicios_personas",
    "seguridad":          "servicios_generales",
    "gobernanza":         "servicios_generales",
    "otro":               "pleno",
}


def clasificar(titulo: str, campo: dict) -> str:
    t = titulo.lower()
    for cat, kws in campo.items():
        if any(k in t for k in kws):
            return cat
    return "otro"

def clasificar_con_comision(titulo: str, cat_comision: str) -> str:
    """Category from keyword match first, then commission fallback."""
    por_keyword = clasificar(titulo, CATS)
    if por_keyword != "otro":
        return por_keyword
    return cat_comision if cat_comision != "otro" else "otro"

def relevancia(titulo: str, categoria: str, resultado: str = "sin_votacion") -> int:
    t = titulo.lower()
    if categoria in ("vivienda", "servicios_sociales", "derechos", "medio_ambiente"):
        return 4
    if categoria in ("urbanismo", "hacienda", "movilidad", "seguridad"):
        return 3
    if categoria == "cultura":
        return 2
    if "dar cuenta" in t or resultado == "enterado":
        return 1
    if "nombramiento" in t or "cese" in t or "compatibilidad" in t:
        return 1
    return 2


# ── Extracción de puntos ──────────────────────────────────────────────────────

def _cat_from_line(line_up: str, current: str) -> str:
    for kws, cat in COMISION_CAT_MAP:
        if any(k in line_up for k in kws):
            return cat
    return current


def _extraer_toc_bloque(bloque: str) -> list[dict]:
    """
    Extract punto entries from a bilingual table-of-contents block.
    Returns list of {numero, titulo, cat_override}.
    """
    bloque = re.sub(r"AKTA \d+ ACTA \d+\n[^\n]+\n", "", bloque)
    current_cat = "otro"
    puntos = []
    seen: set[int] = set()

    def _add(num: int, titulo: str, cat: str) -> None:
        if num > 30 or num in seen:
            return
        titulo = re.sub(r"\s+\d+\s*$", "", titulo).strip(" .,")
        if len(titulo) < 8:
            return
        puntos.append({"numero": num, "titulo": titulo[:450], "cat_override": cat})
        seen.add(num)

    for line in bloque.split("\n"):
        ln = line.strip()
        if not ln:
            continue
        ln_up = ln.upper()

        # Update commission if no punto number on this line
        if not re.search(r"\b\d{1,2}\s+[A-Z]", ln):
            current_cat = _cat_from_line(ln_up, current_cat)

        # Extraordinary single-item: Bakarra / Único
        m_bak = re.search(r"(?:Bakarra|[UÚ]nico)\s+(" + _SPANISH + r"[^\n]{5,})", ln, re.I)
        if m_bak:
            titulo = re.sub(r"\s+\d+\s*$", "", m_bak.group(1)).strip(" .,")
            _add(1, titulo, current_cat)
            continue

        # Number mid-line or at start, followed by Spanish trigger
        for m in re.finditer(
            r"(?:(?<=\s)|^)(\d{1,2})\s+(" + _SPANISH + r"[^\n]{5,})",
            ln, re.IGNORECASE | re.MULTILINE
        ):
            _add(int(m.group(1)), m.group(2).strip(), current_cat)

        # Standalone number case: 'SPANISH_TEXT PAGE\nNUM\nPAGE'
        for m in re.finditer(
            r"(" + _SPANISH + r"[^\n]{5,}?)\s*\n(\d{1,2})\n\d+",
            bloque, re.IGNORECASE
        ):
            _add(int(m.group(2)), m.group(1).strip(), current_cat)

    return puntos


def extraer_puntos_completo(texto: str) -> list[dict]:
    """
    Extracts ALL agenda items by combining SUMARIO and PARTE RESOLUTIVA
    table of contents, then enriches with voting results from the body.
    """
    by_num: dict[int, dict] = {}

    # ── 1. From SUMARIO ──────────────────────────────────────────────────────
    m_sum = re.search(
        r"SUMARIO(.{0,7000}?)(?:ERABAKI ZATIA|PARTE RESOLUTIVA\b|---)", texto, re.DOTALL | re.I
    )
    if m_sum:
        for p in _extraer_toc_bloque(m_sum.group(1)):
            by_num[p["numero"]] = p

    # ── 2. From PARTE RESOLUTIVA TOC (richer titles, more points) ────────────
    m_res = re.search(
        r"(?:ERABAKI ZATIA\s*I\s*PARTE RESOLUTIVA|PARTE RESOLUTIVA)\s*\n"
        r"(.*?)(?:SE DECLARA ABIERTA|HASITAKOTZAT JOTZEN DA)",
        texto, re.DOTALL
    )
    if m_res:
        for p in _extraer_toc_bloque(m_res.group(1)):
            num = p["numero"]
            # Prefer longer / more complete title
            if num not in by_num or len(p["titulo"]) > len(by_num[num]["titulo"]):
                by_num[num] = p

    # ── 3. Voting results from body ──────────────────────────────────────────
    votos = _extraer_votos_cuerpo(texto)

    # ── 4. Merge ─────────────────────────────────────────────────────────────
    resultado: list[dict] = []
    for num in sorted(by_num.keys()):
        p = dict(by_num[num])
        v = votos.get(num, {})
        p["resultado"]   = v.get("resultado", "sin_votacion")
        p["unanimidad"]  = v.get("unanimidad")
        p["es_urgencia"] = v.get("es_urgencia", False)
        resultado.append(p)

    # Also add points found only in votos (appear in body but not TOC)
    for num, v in votos.items():
        if num not in by_num and v.get("titulo"):
            resultado.append({
                "numero":      num,
                "titulo":      v["titulo"],
                "cat_override": "otro",
                "resultado":   v.get("resultado", "sin_votacion"),
                "unanimidad":  v.get("unanimidad"),
                "es_urgencia": v.get("es_urgencia", False),
            })

    resultado.sort(key=lambda x: x["numero"])
    return resultado


def _extraer_votos_cuerpo(texto: str) -> dict:
    """
    Parse per-punto voting results from the body (after SE DECLARA ABIERTA).
    Returns {num: {resultado, unanimidad, es_urgencia, titulo}}.
    """
    # Locate body start
    idx = -1
    for marker in ("SE DECLARA ABIERTA", "HASITAKOTZAT JOTZEN DA"):
        i = texto.find(marker)
        if i >= 0:
            idx = i
            break
    if idx < 0:
        return {}

    body = texto[idx:]
    # Split by horizontal rule
    sections = re.split(r"\n-{3,}\n", body)
    results: dict[int, dict] = {}

    for section in sections:
        # Urgency item
        m_urg = re.search(r"Gai Zerrendatik Kanpoko (\d+)\. gaia", section)
        # Normal item: "NUM.-" at start of a line
        m_norm = re.search(r"(?:^|\n)(\d{1,2})\.-\s", section)

        num = None
        es_urgencia = False
        titulo_body = ""

        if m_urg:
            num = int(m_urg.group(1))
            es_urgencia = True
            # Extract Spanish title from urgency header
            m_tit = re.search(
                r"Tratamiento de Urgencia del asunto[^\n]+n[\.º]\s*\d+\s*([A-Z][^\n]{10,})?",
                section
            )
            titulo_body = m_tit.group(0).strip() if m_tit else "Tratamiento de Urgencia"
        elif m_norm:
            num = int(m_norm.group(1))
            # Try to capture title from body header line
            m_tit = re.search(
                r"(?:^|\n)\d{1,2}\.-\s+(?:[^\n]+\n)?\d{1,2}\.-\s+(" + _SPANISH + r"[^\n]{5,})",
                section, re.IGNORECASE
            )
            titulo_body = m_tit.group(1).strip() if m_tit else ""

        if num is None or num > 30:
            continue

        # Parse result
        resultado  = "sin_votacion"
        unanimidad = None
        su = section.upper()

        has_vote_section = bool(
            re.search(r"RESULTADO DE LA VOTACI|BOZKETA.{0,5}EMAITZA", su)
        )

        if has_vote_section:
            if re.search(r"\bAPROBADA?S?\b|\bONARTUA[KN]?\b", su):
                resultado = "aprobado"
                unanimidad = bool(re.search(r"UNANIMIDAD|AHO BATEZ", su))
            elif re.search(r"\bRECHAZADA?S?\b|\bARBUTATUA\b|\bUKATUA\b", su):
                resultado = "rechazado"
                unanimidad = False
            elif re.search(r"\bENTERADO\b|\bJAKINEAN\b", su):
                resultado = "enterado"
            elif re.search(r"\bRETIRADA?\b|\bERRETIRATU\b", su):
                resultado = "retirado"
            elif re.search(r"\bAPLAZADA?\b|\bATZERATU\b", su):
                resultado = "aplazado"
        elif re.search(r"DAR CUENTA|BERRI EMATEA", section[:200], re.I):
            resultado = "enterado"

        results[num] = {
            "resultado":   resultado,
            "unanimidad":  unanimidad,
            "es_urgencia": es_urgencia,
            "titulo":      titulo_body,
        }

    return results


# ── Importación ───────────────────────────────────────────────────────────────

def importar_acta(pdf_path: Path, municipio_id: str) -> bool:
    nombre = pdf_path.name
    print(f"\n{'─'*55}\n  {nombre}\n{'─'*55}")

    print("  Extrayendo texto...", end=" ", flush=True)
    texto   = extraer_texto(pdf_path)
    meta    = extraer_meta(texto, nombre)
    puntos  = extraer_puntos_completo(texto)
    print(f"OK  ({len(texto):,} chars, {len(puntos)} puntos)")

    if not meta.get("numero_acta"):
        print("  No se pudo extraer numero de acta, saltando.")
        return False

    pleno_data = {
        "municipio_id":      municipio_id,
        "numero_acta":       meta["numero_acta"],
        "fecha":             meta["fecha"],
        "tipo_sesion":       meta["tipo_sesion"],
        "hora_inicio":       meta.get("hora_inicio"),
        "alcalde_nombre":    meta.get("alcalde_nombre"),
        "secretaria_nombre": meta.get("secretaria_nombre"),
        "texto_completo":    texto[:50000],
        "resumen_ia":        None,
        "n_puntos":          len(puntos),
        "n_asistentes":      meta.get("n_asistentes"),
        "n_ausentes":        meta.get("n_ausentes"),
        "url_pdf_original":  "https://www.donostia.eus/secretaria/asuntospleno.nsf/",
        "estado":            "procesado",
    }

    print("  Insertando pleno...", end=" ", flush=True)
    try:
        pleno = sb_post("plenos", pleno_data)
        pleno_id = pleno["id"]
        print(f"OK  (id: {pleno_id[:8]})")
    except httpx.HTTPStatusError as e:
        if "duplicate" in e.response.text.lower() or "unique" in e.response.text.lower():
            print("ya existe.")
            rows = sb_get("plenos", {"numero_acta": f"eq.{meta['numero_acta']}", "select": "id"})
            pleno_id = rows[0]["id"] if rows else None
            if not pleno_id:
                return True
        else:
            print(f"\n  Error: {e.response.text[:200]}")
            return False

    # Delete existing puntos and re-insert
    try:
        sb_delete("puntos", {"pleno_id": pleno_id})
    except Exception:
        pass

    print(f"  Insertando {len(puntos)} puntos...", end=" ", flush=True)
    ok_pts = 0
    for p in puntos:
        cat  = clasificar_con_comision(p["titulo"], p.get("cat_override", "otro"))
        tipo = clasificar(p["titulo"], TIPOS)
        com  = COMISION_SCHEMA.get(cat, "pleno")
        res  = p.get("resultado", "sin_votacion")
        try:
            sb_post("puntos", {
                "pleno_id":          pleno_id,
                "numero":            p["numero"],
                "titulo":            p["titulo"][:500],
                "categoria":         cat,
                "tipo":              tipo,
                "comision":          com,
                "resultado":         res,
                "unanimidad":        p.get("unanimidad"),
                "resumen_ia":        None,
                "relevancia_social": relevancia(p["titulo"], cat, res),
                "es_urgencia":       p.get("es_urgencia", False),
            })
            ok_pts += 1
        except Exception as e:
            pass
    print(f"OK  ({ok_pts}/{len(puntos)} insertados)")

    # Update n_puntos on pleno
    try:
        sb_patch("plenos", {"id": pleno_id}, {"n_puntos": ok_pts})
    except Exception:
        pass

    print(f"  Acta {meta['numero_acta']} importada ({meta['fecha']})")
    return True


def main():
    print("\n" + "="*55 + "\n  Acta Civium — Importacion de actas\n" + "="*55)

    municipios = sb_get("municipios", {"nombre": "eq.San Sebastián", "select": "id"})
    if not municipios:
        print("No se encuentra el municipio. Ejecuta el schema.sql en Supabase.")
        sys.exit(1)
    municipio_id = municipios[0]["id"]
    print(f"\n  Municipio: San Sebastian (id: {municipio_id[:8]})")

    pdfs = sorted(ACTAS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No hay PDFs en {ACTAS_DIR}")
        sys.exit(1)

    ok, err = 0, 0
    for pdf in pdfs:
        if importar_acta(pdf, municipio_id):
            ok += 1
        else:
            err += 1
        time.sleep(0.3)

    print(f"\n{'='*55}\n  Completado: {ok} actas, {err} errores\n{'='*55}\n")


if __name__ == "__main__":
    main()
