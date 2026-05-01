"""
Extrae texto de PDFs de actas municipales y genera resúmenes con Claude CLI.
"""
import re
import subprocess
import json
import pdfplumber
from pathlib import Path
from config import CLAUDE_CMD, PDF_MAX_PAGES_FOR_SUMMARY


# ── Extracción de texto ───────────────────────────────────────────────────────

def extraer_texto(pdf_path: Path) -> str:
    """Extrae todo el texto de un PDF, limpiando artefactos de Lotus Notes."""
    partes = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=2, y_tolerance=2)
            if texto:
                partes.append(texto)
    texto_completo = "\n".join(partes)
    return _limpiar_texto(texto_completo)


def _limpiar_texto(texto: str) -> str:
    # Eliminar encabezados repetidos de cada página (AKTA XX / ACTA XX + fecha)
    texto = re.sub(r"AKTA \d+ ACTA \d+\n[^\n]+\n", "", texto)
    # Colapsar más de 3 saltos de línea consecutivos
    texto = re.sub(r"\n{4,}", "\n\n\n", texto)
    # Normalizar espacios
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()


# ── Parsing estructurado ──────────────────────────────────────────────────────

def extraer_metadatos(texto: str) -> dict:
    """Extrae campos de cabecera del acta a partir del texto completo."""
    meta = {}

    m = re.search(r"ACTA\s+(\d+)", texto)
    if m:
        meta["numero_acta"] = int(m.group(1))

    m = re.search(r"(\d{1,2}) DE (\w+) DE (\d{4})", texto, re.IGNORECASE)
    if m:
        meta["fecha_raw"] = f"{m.group(1)} {m.group(2)} {m.group(3)}"

    m = re.search(r"SESI[ÓO]N:\s*(Ordinaria|Extraordinaria|Urgente)", texto, re.IGNORECASE)
    if m:
        tipo = m.group(1).lower()
        meta["tipo_sesion"] = {
            "ordinaria": "ordinaria",
            "extraordinaria": "extraordinaria",
            "urgente": "urgente",
        }.get(tipo, "ordinaria")

    m = re.search(r"HORA DE COMIENZO:\s*(\d{1,2}:\d{2})", texto)
    if m:
        meta["hora_inicio"] = m.group(1)

    m = re.search(r"PRESIDE:\s*Don(?:a)?\s+([^\n,]+)", texto)
    if m:
        meta["alcalde_nombre"] = m.group(1).strip()

    m = re.search(r"SECRETARIA?:\s*Do[ñn]a?\s+([^\n,]+)", texto)
    if m:
        meta["secretaria_nombre"] = m.group(1).strip()

    return meta


def extraer_asistentes(texto: str) -> tuple[list[str], list[str]]:
    """Devuelve (asistentes, ausentes) como listas de nombres raw."""
    asistentes, ausentes = [], []

    bloque_asisten = re.search(
        r"ASISTEN:(.+?)(?:NO ASISTE|SECRETARIA)", texto, re.DOTALL
    )
    if bloque_asisten:
        bloque = bloque_asisten.group(1)
        asistentes = re.findall(r"Don(?:a|ña)?\s+([A-ZÁÉÍÓÚÑÜ][^\n]+)", bloque)

    bloque_ausentes = re.search(
        r"NO ASISTE[NS]?:(.+?)(?:SECRETARIA|IDAZKARIA)", texto, re.DOTALL
    )
    if bloque_ausentes:
        bloque = bloque_ausentes.group(1)
        ausentes = re.findall(r"Don(?:a|ña)?\s+([A-ZÁÉÍÓÚÑÜ][^\n]+)", bloque)

    return [n.strip() for n in asistentes], [n.strip() for n in ausentes]


def extraer_puntos_sumario(texto: str) -> list[dict]:
    """
    Extrae los puntos del sumario (índice).
    Devuelve lista de {numero, titulo, pagina}.
    """
    puntos = []

    # El sumario está entre SUMARIO y la primera sección resolutiva
    m = re.search(r"SUMARIO(.+?)(?:PARTE RESOLUTIVA|INFORMACIÓN, IMPULSO)", texto, re.DOTALL)
    if not m:
        return puntos

    bloque = m.group(1)

    # Patrón: número + título en español + número de página
    patron = re.compile(
        r"(\d+)\s{2,}([A-ZÁÉÍÓÚÑÜ][^\d\n]{10,}?)\s{2,}(\d+)",
        re.MULTILINE
    )
    for match in patron.finditer(bloque):
        puntos.append({
            "numero": int(match.group(1)),
            "titulo": _limpiar_titulo(match.group(2)),
            "pagina": int(match.group(3)),
        })

    return puntos


def _limpiar_titulo(titulo: str) -> str:
    return re.sub(r"\s+", " ", titulo).strip(" .,")


def extraer_votaciones_texto(texto: str) -> list[dict]:
    """
    Busca todos los bloques 'RESULTADO DE LA VOTACIÓN' y extrae el resultado.
    Devuelve lista de {resultado, unanimidad, detalle_raw}.
    """
    votaciones = []
    patron = re.compile(
        r"RESULTADO DE LA VOTACI[ÓO]N:\s*\n(.*?)(?=RESULTADO DE LA VOTACI[ÓO]N|---|\Z)",
        re.DOTALL | re.IGNORECASE
    )
    for m in patron.finditer(texto):
        bloque = m.group(1).strip()
        entrada = {
            "resultado": _parsear_resultado(bloque),
            "unanimidad": "UNANIMIDAD" in bloque.upper() or "AHO BATEZ" in bloque.upper(),
            "detalle_raw": bloque[:500],
            "partidos": _parsear_votos_partido(bloque),
        }
        votaciones.append(entrada)

    return votaciones


def _parsear_resultado(bloque: str) -> str:
    bloque_up = bloque.upper()
    if "APROBAD" in bloque_up or "ONARTU" in bloque_up:
        return "aprobado"
    if "RECHAZAD" in bloque_up or "EZETSID" in bloque_up:
        return "rechazado"
    if "ENTERADO" in bloque_up or "JAKINTZE" in bloque_up:
        return "enterado"
    if "RETIR" in bloque_up:
        return "retirado"
    return "sin_votacion"


def _parsear_votos_partido(bloque: str) -> list[dict]:
    """Extrae votos por partido cuando hay desglose explícito."""
    partidos = []
    # Patrón: "votos a favor de EAJ/PNV, PSE-EE"
    favor = re.findall(r"(?:votos? a favor|aldeko bozkak?) de(?:l grupo)?s? ([A-ZÁÉÍÓÚÑÜ/,\s\-]+?)(?:y los|y el|$)", bloque, re.IGNORECASE)
    contra = re.findall(r"(?:votos? en contra|aurkako bozkak?) de(?:l grupo)?s? ([A-ZÁÉÍÓÚÑÜ/,\s\-]+?)(?:y los|y el|\.|$)", bloque, re.IGNORECASE)

    for grupo in favor:
        for sigla in re.split(r",\s*|\s+y\s+", grupo):
            sigla = sigla.strip()
            if sigla:
                partidos.append({"siglas": sigla, "posicion": "favor"})

    for grupo in contra:
        for sigla in re.split(r",\s*|\s+y\s+", grupo):
            sigla = sigla.strip()
            if sigla:
                partidos.append({"siglas": sigla, "posicion": "contra"})

    return partidos


# ── Clasificación temática ────────────────────────────────────────────────────

CATEGORIAS_KEYWORDS = {
    "vivienda": ["vivienda", "etxebizitza", "alquiler", "tasada", "habitacional", "inquilino"],
    "urbanismo": ["urbanismo", "plan general", "pgou", "ordenación", "parcela", "estudio de detalle", "ámbito urbanístico"],
    "hacienda": ["ordenanza fiscal", "impuesto", "tasa", "presupuesto", "iva", "ibo", "icio", "iae"],
    "medio_ambiente": ["medio ambiente", "sostenibilidad", "residuos", "bioresiduo", "reciclaje", "emisiones", "clima", "verde"],
    "servicios_sociales": ["servicios sociales", "bienestar", "ayuda", "dependencia", "exclusión", "vulnerabl", "pobreza"],
    "movilidad": ["movilidad", "transporte", "tráfico", "ota", "aparcamiento", "bus", "bicicleta", "peatonal"],
    "cultura": ["cultura", "kultura", "festival", "museo", "deporte", "educación"],
    "derechos": ["derechos", "igualdad", "género", "violencia", "lgtbi", "discriminación", "mujer", "diversidad"],
    "gobernanza": ["delegación", "compatibilidad", "nombramiento", "cese", "concejal", "alcalde", "junta de gobierno"],
    "seguridad": ["policía", "seguridad", "bomberos", "emergencias", "protección civil"],
}


def clasificar_categoria(titulo: str, texto: str = "") -> str:
    contenido = (titulo + " " + texto).lower()
    for categoria, keywords in CATEGORIAS_KEYWORDS.items():
        if any(kw in contenido for kw in keywords):
            return categoria
    return "otro"


def clasificar_tipo(titulo: str) -> str:
    t = titulo.lower()
    if "aprobación definitiva" in t or "behin-betiko" in t:
        return "aprobacion_definitiva"
    if "aprobación inicial" in t or "hasierako" in t:
        return "aprobacion_inicial"
    if "dar cuenta" in t or "berri ematea" in t:
        return "dar_cuenta"
    if "proposición normativa" in t or "arau proposamena" in t:
        return "proposicion_normativa"
    if "moción" in t:
        return "mocion"
    if "ruego" in t:
        return "ruego"
    if "pregunta" in t:
        return "pregunta_oral"
    if "interpelación" in t:
        return "interpelacion"
    if "declaración institucional" in t or "erakunde adierazpen" in t:
        return "declaracion_institucional"
    return "otro"


def clasificar_comision(titulo: str) -> str:
    t = titulo.lower()
    if "territorio" in t or "planificaci" in t or "lurralde" in t:
        return "territorio"
    if "servicios a las personas" in t or "pertsonentzako" in t:
        return "servicios_personas"
    if "servicios generales" in t or "zerbitzu orokor" in t:
        return "servicios_generales"
    if "hacienda" in t or "ogasun" in t:
        return "hacienda"
    if "información" in t or "impulso" in t or "control" in t:
        return "informacion_control"
    return "pleno"


# ── Resumen con Claude CLI ────────────────────────────────────────────────────

PROMPT_RESUMEN_PLENO = """Eres el redactor de Acta Civium, una publicación ciudadana que analiza los plenos municipales desde una perspectiva social, ambiental y de responsabilidad pública.

Analiza el siguiente texto de un acta de pleno municipal y genera un resumen estructurado en JSON con este formato exacto:

{{
  "resumen_pleno": "2-3 frases. Qué temas dominaron el pleno, qué decisiones clave se tomaron y cuál es su impacto ciudadano. Tono neutro pero con mirada crítica hacia el impacto social y ambiental.",
  "puntos": [
    {{
      "numero": <número del punto>,
      "titulo": "<título limpio en castellano>",
      "categoria": "<una de: urbanismo|vivienda|hacienda|medio_ambiente|servicios_sociales|movilidad|cultura|gobernanza|derechos|seguridad|educacion|otro>",
      "tipo": "<una de: aprobacion_definitiva|aprobacion_inicial|dar_cuenta|proposicion_normativa|mocion|ruego|pregunta_oral|declaracion_institucional|otro>",
      "comision": "<una de: territorio|servicios_personas|servicios_generales|hacienda|informacion_control|pleno>",
      "resultado": "<una de: aprobado|rechazado|enterado|retirado|sin_votacion>",
      "unanimidad": <true|false>,
      "relevancia_social": <1-5>,
      "resumen_ia": "<1-2 frases explicando qué se decidió y por qué importa a la ciudadanía. Enfocado en impacto real: vivienda, servicios, presupuesto, medio ambiente, derechos.>"
    }}
  ]
}}

CRITERIOS DE RELEVANCIA SOCIAL (1-5):
- 5: Decisiones que afectan directamente a colectivos vulnerables, al acceso a vivienda, al medio ambiente, a derechos fundamentales, o que implican grandes partidas presupuestarias.
- 4: Cambios en ordenanzas fiscales con impacto ciudadano amplio, urbanismo con impacto en barrios, servicios sociales.
- 3: Aprobación de planes o reglamentos de alcance medio.
- 2: Trámites administrativos con algún impacto indirecto.
- 1: Trámites puramente internos (compatibilidades, nombramientos técnicos, etc.).

IMPORTANTE:
- Solo incluye en "puntos" los del PARTE RESOLUTIVA (no "dar cuenta" administrativos sin relevancia).
- Escribe los resúmenes en castellano, lenguaje ciudadano, sin jerga burocrática.
- Destaca cuando un punto fue rechazado por la mayoría o aprobado solo con votos del gobierno.
- Si hay impacto en colectivos vulnerables, menciónalo explícitamente.

TEXTO DEL ACTA (primeras {max_pages} páginas):
{texto}
"""

PROMPT_RESUMEN_PUNTO = """Eres el redactor de Acta Civium. En 1-2 frases, explica este punto del orden del día de un pleno municipal desde una perspectiva ciudadana: qué se decidió, por qué importa, a quién afecta. Sin jerga burocrática.

Título: {titulo}
Resultado: {resultado}
Texto: {texto}
"""


def generar_resumen_pleno(texto: str, max_pages: int = PDF_MAX_PAGES_FOR_SUMMARY) -> dict | None:
    """Llama a Claude CLI para generar el resumen estructurado del pleno."""
    # Limitamos el texto para no exceder el contexto
    texto_recortado = _recortar_texto(texto, max_chars=120_000)
    prompt = PROMPT_RESUMEN_PLENO.format(texto=texto_recortado, max_pages=max_pages)

    resultado = _llamar_claude(prompt)
    if not resultado:
        return None

    try:
        # Claude puede devolver el JSON envuelto en markdown
        json_str = re.search(r"\{.*\}", resultado, re.DOTALL)
        if json_str:
            return json.loads(json_str.group())
    except json.JSONDecodeError:
        pass

    return None


def generar_resumen_punto(titulo: str, resultado: str, texto: str) -> str | None:
    """Genera resumen corto de un punto individual."""
    texto_recortado = _recortar_texto(texto, max_chars=8_000)
    prompt = PROMPT_RESUMEN_PUNTO.format(
        titulo=titulo, resultado=resultado, texto=texto_recortado
    )
    return _llamar_claude(prompt)


def _llamar_claude(prompt: str) -> str | None:
    """Ejecuta Claude CLI de forma no interactiva y devuelve la respuesta."""
    try:
        result = subprocess.run(
            [CLAUDE_CMD, "-p", prompt, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _recortar_texto(texto: str, max_chars: int) -> str:
    if len(texto) <= max_chars:
        return texto
    # Intentar cortar en un salto de línea limpio
    corte = texto.rfind("\n", 0, max_chars)
    return texto[: corte if corte > 0 else max_chars]
