"""
Script de importación directa de las 5 actas de muestra a Supabase.
Usa httpx + REST API directamente (sin cliente supabase-py).

Uso:
  cd actacivium/scraper
  python import_actas.py
"""
import re
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import httpx
import pdfplumber
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/").removesuffix("/rest/v1")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ACTAS_DIR   = Path(__file__).parent.parent.parent / "actas_muestra"

if not SUPABASE_URL or SUPABASE_URL == "https://xxxxxxxxxxxx.supabase.co":
    print("❌  Rellena SUPABASE_URL y SUPABASE_KEY en el archivo .env")
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

    # Número de acta desde el nombre del archivo: acta_39_20251030.pdf
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

    asistentes = re.findall(r"Don(?:a|ña)?\s+([A-ZÁÉÍÓÚÑÜ][^\n]{5,40})", texto[:3000])
    ausentes   = re.findall(r"NO ASISTE[NS]?:(.+?)SECRETARIA", texto, re.DOTALL)
    meta["n_asistentes"] = len(asistentes)
    meta["n_ausentes"]   = len(re.findall(r"Don(?:a|ña)?", ausentes[0])) if ausentes else 0

    return meta

_SPANISH = (
    r"(?:Aprobaci|Dar\s+cuenta|Toma\s+de|Declaraci|Proposici|Moci|Tratamiento|"
    r"Modificaci|Informaci|Debate|Ratificaci|Acuerdo|Adjudicaci|Contrataci|"
    r"Subvenci|Ordenanza|Presupuest|Plan\s|Convenio|Concesi|Daci|Resoluci|"
    r"Nombramiento|Autorizaci|Desestimaci|Licencia)"
)

def extraer_sumario(texto: str) -> list[dict]:
    puntos: list[dict] = []
    seen: set[int] = set()

    m = re.search(r"SUMARIO(.{0,7000}?)(?:ERABAKI ZATIA|PARTE RESOLUTIVA|---)", texto, re.DOTALL | re.I)
    if not m:
        return puntos
    bloque = m.group(1)
    bloque = re.sub(r"AKTA \d+ ACTA \d+\n[^\n]+\n", "", bloque)

    # Extraordinary single-item session (Bakarra / Único)
    if re.search(r"Bakarra|[UÚ]nico", bloque, re.I):
        m2 = re.search(r"(?:Bakarra|[UÚ]nico)\s+(" + _SPANISH + r"[^\n]{5,})", bloque, re.I)
        if m2:
            titulo = re.sub(r"\s+\d+\s*$", "", m2.group(1)).strip(" .,")
            return [{"numero": 1, "titulo": titulo[:300]}]

    def _add(num: int, titulo: str) -> None:
        if num > 30 or num in seen:
            return
        titulo = re.sub(r"\s+\d+\s*$", "", titulo).strip(" .,")
        puntos.append({"numero": num, "titulo": titulo[:300]})
        seen.add(num)

    # Number at line-start or mid-line followed by Spanish-trigger text
    for match in re.finditer(
        r"(?:(?<=\s)|^)(\d{1,2})\s+(" + _SPANISH + r"[^\n]{5,})",
        bloque, re.MULTILINE | re.IGNORECASE
    ):
        _add(int(match.group(1)), match.group(2).strip())

    # Standalone number on its own line: 'SPANISH_TEXT PAGE\nNUM\nNEXT_PAGE'
    for match in re.finditer(
        r"(" + _SPANISH + r"[^\n]{5,}?)\s*\n(\d{1,2})\n\d+",
        bloque, re.IGNORECASE
    ):
        _add(int(match.group(2)), match.group(1).strip())

    puntos.sort(key=lambda x: x["numero"])
    return puntos

CATS = {
    "vivienda":           ["vivienda","etxebizitza","alquiler","tasada","habitacional"],
    "urbanismo":          ["urbanismo","plan general","pgou","ordenación","parcela","estudio de detalle"],
    "hacienda":           ["ordenanza fiscal","impuesto","tasa","presupuesto","ibo","icio","iae"],
    "medio_ambiente":     ["medio ambiente","residuos","bioresiduo","reciclaje","emisiones","clima"],
    "servicios_sociales": ["servicios sociales","bienestar","ayuda","dependencia","exclusión","vulnerabl"],
    "movilidad":          ["movilidad","transporte","tráfico","ota","aparcamiento","bus","bicicleta"],
    "cultura":            ["cultura","festival","museo","deporte","educación"],
    "derechos":           ["derechos","igualdad","género","violencia","lgtbi","discriminación","mujer"],
    "gobernanza":         ["delegación","compatibilidad","nombramiento","cese","concejal","alcalde"],
}
TIPOS = {
    "aprobacion_definitiva":  ["aprobación definitiva","behin-betiko"],
    "aprobacion_inicial":     ["aprobación inicial","hasierako"],
    "dar_cuenta":             ["dar cuenta","berri ematea"],
    "proposicion_normativa":  ["proposición normativa","arau proposamena"],
    "mocion":                 ["moción"],
    "declaracion_institucional": ["declaración institucional","erakunde adierazpen"],
}

def clasificar(titulo: str, campo: dict) -> str:
    t = titulo.lower()
    for cat, kws in campo.items():
        if any(k in t for k in kws):
            return cat
    return "otro"

def relevancia(titulo: str, categoria: str) -> int:
    t = titulo.lower()
    if categoria in ("vivienda", "servicios_sociales", "derechos", "medio_ambiente"):
        return 4
    if categoria in ("urbanismo", "hacienda", "movilidad"):
        return 3
    if "dar cuenta" in t or "compatibilidad" in t or "nombramiento" in t:
        return 1
    return 2


# ── Importación ───────────────────────────────────────────────────────────────

def importar_acta(pdf_path: Path, municipio_id: str) -> bool:
    nombre = pdf_path.name
    print(f"\n{'─'*55}")
    print(f"  {nombre}")
    print(f"{'─'*55}")

    # Extraer texto
    print("  ↳ Extrayendo texto...", end=" ", flush=True)
    texto = extraer_texto(pdf_path)
    meta  = extraer_meta(texto, nombre)
    sumario = extraer_sumario(texto)
    print(f"OK  ({len(texto):,} chars, {len(sumario)} puntos)")

    if not meta.get("numero_acta"):
        print("  ✗ No se pudo extraer número de acta, saltando.")
        return False

    # Insertar pleno
    pleno_data = {
        "municipio_id":       municipio_id,
        "numero_acta":        meta["numero_acta"],
        "fecha":              meta["fecha"],
        "tipo_sesion":        meta["tipo_sesion"],
        "hora_inicio":        meta.get("hora_inicio"),
        "alcalde_nombre":     meta.get("alcalde_nombre"),
        "secretaria_nombre":  meta.get("secretaria_nombre"),
        "texto_completo":     texto[:50000],   # supabase free: columnas grandes tienen límite
        "resumen_ia":         None,
        "n_puntos":           len(sumario),
        "n_asistentes":       meta.get("n_asistentes"),
        "n_ausentes":         meta.get("n_ausentes"),
        "url_pdf_original":   f"https://www.donostia.eus/secretaria/asuntospleno.nsf/",
        "estado":             "procesado",
    }

    print("  ↳ Insertando pleno en Supabase...", end=" ", flush=True)
    try:
        pleno = sb_post("plenos", pleno_data)
        pleno_id = pleno["id"]
        print(f"OK  (id: {pleno_id[:8]}…)")
    except httpx.HTTPStatusError as e:
        if "duplicate" in e.response.text.lower() or "unique" in e.response.text.lower():
            print("ya existe, saltando.")
            return True
        print(f"\n  ✗ Error: {e.response.text[:200]}")
        return False

    # Insertar puntos
    print(f"  ↳ Insertando {len(sumario)} puntos...", end=" ", flush=True)
    for p in sumario:
        cat  = clasificar(p["titulo"], CATS)
        tipo = clasificar(p["titulo"], TIPOS)
        try:
            sb_post("puntos", {
                "pleno_id":         pleno_id,
                "numero":           p["numero"],
                "titulo":           p["titulo"][:500],
                "categoria":        cat,
                "tipo":             tipo,
                "comision":         "pleno",
                "resultado":        "sin_votacion",
                "unanimidad":       None,
                "resumen_ia":       None,
                "relevancia_social": relevancia(p["titulo"], cat),
                "es_urgencia":      False,
            })
        except Exception:
            pass   # si falla un punto individual, continuamos
    print("OK")

    print(f"  ✓ Acta {meta['numero_acta']} importada ({meta['fecha']})")
    return True


def main():
    print("\n" + "═"*55)
    print("  Acta Civium — Importación de actas de muestra")
    print("═"*55)

    # Obtener municipio_id
    municipios = sb_get("municipios", {"nombre": "eq.San Sebastián", "select": "id"})
    if not municipios:
        print("❌  No se encuentra el municipio 'San Sebastián' en la BD.")
        print("    ¿Has ejecutado el schema.sql en Supabase?")
        sys.exit(1)
    municipio_id = municipios[0]["id"]
    print(f"\n  Municipio: San Sebastián (id: {municipio_id[:8]}…)")

    # Procesar cada PDF
    pdfs = sorted(ACTAS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"❌  No hay PDFs en {ACTAS_DIR}")
        sys.exit(1)

    ok, err = 0, 0
    for pdf in pdfs:
        if importar_acta(pdf, municipio_id):
            ok += 1
        else:
            err += 1
        time.sleep(0.5)

    print(f"\n{'═'*55}")
    print(f"  Completado: {ok} actas importadas, {err} errores")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
