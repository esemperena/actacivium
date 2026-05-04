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


_RE_GRUPO = re.compile(
    r"(?:GRUPO\s+MUNICIPAL|MUNICIPAL\s+TALDEA?|TALDE\s+UDALA?)[:\s]+([A-ZÁÉÍÓÚÑÜ\w][^\n:]{2,60})",
    re.IGNORECASE,
)
_RE_NOMBRE = re.compile(r"Don(?:a|ña)?\s+([A-ZÁÉÍÓÚÑÜ][^\n,]{3,50})")


def extraer_asistentes_con_partido(texto: str) -> list[dict]:
    """
    Extrae concejales con partido y asistencia del encabezado del acta.
    Devuelve lista de {nombre, partido_raw, asistio}.
    partido_raw puede ser None si el acta no agrupa por grupos municipales.
    """
    def _parsear_bloque(bloque: str, asistio: bool) -> list[dict]:
        registros = []
        partido_actual: str | None = None
        for linea in bloque.split("\n"):
            m_grupo = _RE_GRUPO.search(linea)
            if m_grupo:
                partido_actual = m_grupo.group(1).strip()
                continue
            for m_nom in _RE_NOMBRE.finditer(linea):
                registros.append({
                    "nombre": m_nom.group(1).strip(),
                    "partido_raw": partido_actual,
                    "asistio": asistio,
                })
        return registros

    resultado = []
    m = re.search(r"ASISTEN:(.+?)(?:NO ASISTE|SECRETARIA|IDAZKARIA)", texto, re.DOTALL)
    if m:
        resultado.extend(_parsear_bloque(m.group(1), True))
    m = re.search(r"NO ASISTE[NS]?:(.+?)(?:SECRETARIA|IDAZKARIA)", texto, re.DOTALL)
    if m:
        resultado.extend(_parsear_bloque(m.group(1), False))
    return resultado


def extraer_asistentes(texto: str) -> tuple[list[str], list[str]]:
    """Devuelve (asistentes, ausentes) como listas de nombres raw."""
    registros = extraer_asistentes_con_partido(texto)
    if registros:
        return (
            [r["nombre"] for r in registros if r["asistio"]],
            [r["nombre"] for r in registros if not r["asistio"]],
        )
    # Fallback: regex directo sin agrupación por partido
    asistentes, ausentes = [], []
    m = re.search(r"ASISTEN:(.+?)(?:NO ASISTE|SECRETARIA)", texto, re.DOTALL)
    if m:
        asistentes = re.findall(r"Don(?:a|ña)?\s+([A-ZÁÉÍÓÚÑÜ][^\n]+)", m.group(1))
    m = re.search(r"NO ASISTE[NS]?:(.+?)(?:SECRETARIA|IDAZKARIA)", texto, re.DOTALL)
    if m:
        ausentes = re.findall(r"Don(?:a|ña)?\s+([A-ZÁÉÍÓÚÑÜ][^\n]+)", m.group(1))
    return [n.strip() for n in asistentes], [n.strip() for n in ausentes]


def extraer_puntos_sumario(texto: str) -> list[dict]:
    """
    Extrae los puntos del orden del día desde el sumario del acta.
    El layout bilingüe intercala Basque y castellano en cada línea.
    Patrón en el sumario: "euskera_text NUM spanish_text [PAGE]"
    Devuelve lista de {numero, titulo, pagina}.
    """
    # Acota el bloque del sumario
    m_inicio = re.search(r"\bSUMARIO\b", texto, re.IGNORECASE)
    if not m_inicio:
        return []
    m_fin = re.search(r"-{3,}|DONOSTIAKO UDALBATZAR|SE DECLARA ABIERTA", texto[m_inicio.end():])
    fin = m_inicio.end() + m_fin.start() if m_fin else m_inicio.end() + 4000
    bloque = texto[m_inicio.end(): fin]

    vistos: set[int] = set()
    puntos = []

    # Caso especial: sesión con un único punto ("Bakarra / Único")
    m_unico = re.search(r"(?:Bakarra|[ÚU]nico)\s+([A-ZÁÉÍÓÚÑÜ][^\n]{5,})", bloque, re.I)
    if m_unico:
        titulo = re.sub(r"\s+\d{1,3}\s*$", "", m_unico.group(1)).strip()
        puntos.append({"numero": 1, "titulo": _limpiar_titulo(titulo), "pagina": None})
        return puntos

    # Cada entrada tiene: "basque_text NUM spanish_text PAGE?" en una o varias líneas
    # Buscamos el número como separador entre columnas bilingües
    patron = re.compile(r"\b(\d{1,2})\s+([A-ZÁÉÍÓÚÑÜ][^\n]{5,})")
    lineas = bloque.split("\n")

    for i, linea in enumerate(lineas):
        m = patron.search(linea)
        if not m:
            continue
        num = int(m.group(1))
        if num in vistos:
            continue

        # Título: texto castellano de esta línea (tras el número), sin el número de página final
        titulo_base = re.sub(r"\s+\d{1,3}\s*$", "", m.group(2)).strip()

        # Extender siempre: los títulos del sumario terminan en punto; parar en nueva entrada
        _complete_end = re.compile(r'[."\)»]$')
        _new_entry = re.compile(r"\b\d{1,2}\s+[A-ZÁÉÍÓÚÑÜ]")
        _page_end = re.compile(r"\s\d{1,3}$")  # línea que termina con nº de página = nueva entrada
        for j in range(i + 1, min(i + 8, len(lineas))):
            if _complete_end.search(titulo_base):
                break
            cont = lineas[j].strip()
            if not cont:
                continue
            if _new_entry.search(cont) or _page_end.search(cont):
                break
            segmento = _segmento_espanol_sumario(cont)
            if segmento:
                segmento = re.sub(r"\s+\d{1,3}\s*$", "", segmento).strip()
                titulo_base = (titulo_base + " " + segmento).strip()

        vistos.add(num)
        puntos.append({
            "numero": num,
            "titulo": _limpiar_titulo(titulo_base),
            "pagina": None,
        })

    return sorted(puntos, key=lambda p: p["numero"])


def _segmento_espanol_sumario(linea: str) -> str:
    """Extrae la parte castellana de una línea bilingüe del sumario."""
    # 1. Split en "palabra_vasca. " (fin de frase vasca con punto)
    partes = re.split(r"[a-záéíóúüñ]{3,}\.\s+", linea, maxsplit=1)
    if len(partes) > 1 and len(partes[1].strip()) >= 3:
        return partes[1].strip()

    # 2. Anclar en patrones típicamente castellanos: prep. compuestas, acento, mayúscula acentuada
    m = re.search(
        r"\b(?:del\s|de\s+la\s|de\s+los\s|de\s+las\s|para\s+el\b|para\s+la\b|"
        r"al\s+amparo\b|mediante\s|puntual\b|Urbana\b|Ciudad\b|"
        r"[A-ZÁÉÍÓÚÑÜ]\w*[áéíóúñ]\w*)",
        linea,
    )
    if m:
        start = m.start()
        # Incluir la palabra anterior si no tiene sufijo vasco típico
        pre = linea[:start].rstrip()
        last_word = re.search(r"\S+$", pre)
        if last_word:
            lw = last_word.group()
            if not re.search(r"(eko|ean|ko|ren|aren|tzea|tze|rik|ak|ok)$", lw, re.I):
                start = last_word.start()
        return linea[start:].strip()

    # 3. Sustantivos/adjetivos castellanos conocidos en actas municipales
    m = re.search(
        r"\b(?:Grupo\s+\S+|Reglamento|Municipal|Especial|Ordenanza|"
        r"Modificaci[oó]n|[áA]mbito|[aA]rt[ií]culo|sesión|polígono|movilidad|"
        r"Inmuebles|Bienes|Impuesto|Abastecimiento|Saneamiento|Renta|"
        r"Veh[ií]culos|Tráfico|interoperabilidad|relativa|parcela|"
        r"descuento|necesidades|Ayuntamiento|celebrada|Loiola\b|Urgente)",
        linea,
    )
    if m:
        return linea[m.start():].strip()

    # 4. Línea corta sin sufijos vascos = texto castellano puro (columna derecha sin texto vasco)
    if (len(linea) >= 5
            and not re.match(r"^\d{1,3}\.?$", linea)
            and not re.search(r"(eko|ean|ko|ren|aren|tzea|tze|rik|ak|ok)\b", linea, re.I)):
        return linea

    return ""


def _limpiar_titulo(titulo: str) -> str:
    return re.sub(r"\s+", " ", titulo).strip(" .,")


def extraer_votaciones_por_punto(texto: str) -> dict[int, dict]:
    """
    Devuelve {numero_punto: {resultado, unanimidad, partidos, total_abstenciones}}
    asociando cada bloque de votación con el punto del orden del día que le precede.
    Maneja el layout bilingüe (euskera + castellano) de las actas de Donostia.
    """
    result: dict[int, dict] = {}

    # Localizar los encabezados de punto en el cuerpo del acta: "N.-"
    heading_pat = re.compile(r"\b(\d{1,2})\.-\s+[A-ZÁÉÍÓÚÑÜ]")
    headings: list[tuple[int, int]] = []
    seen_nums: set[int] = set()
    for m in heading_pat.finditer(texto):
        num = int(m.group(1))
        if num not in seen_nums:
            seen_nums.add(num)
            headings.append((num, m.start()))

    headings.append((0, len(texto)))  # centinela final

    for i, (num, start) in enumerate(headings[:-1]):
        section = texto[start: headings[i + 1][1]]
        # Tomar el ÚLTIMO bloque de votación de la sección (tras enmiendas)
        vote_starts = [m.start() for m in re.finditer(
            r"RESULTADO DE LA VOTACI[ÓO]N:", section, re.IGNORECASE)]
        if not vote_starts:
            continue
        vote_text = section[vote_starts[-1]:]
        end = re.search(r"-{3,}", vote_text)
        if end:
            vote_text = vote_text[:end.start()]
        vot = _parsear_bloque_votacion(vote_text)
        if vot:
            result[num] = vot

    return result


def _parsear_bloque_votacion(bloque: str) -> dict | None:
    """
    Parsea un bloque 'RESULTADO DE LA VOTACIÓN:...' en el formato Donostia.
    El layout bilingüe duplica el contenido en cada línea; colapsamos y usamos
    los marcadores en castellano (VOTOS A FAVOR, VOTOS EN CONTRA, ABSTENCIONES).
    """
    texto = " ".join(bloque.split())  # colapsar saltos de línea

    resultado = "sin_votacion"
    if re.search(r"APROBAD[AO]", texto, re.I):
        resultado = "aprobado"
    elif re.search(r"RECHAZAD[AO]|BAZTERTUA", texto, re.I):
        resultado = "rechazado"
    elif re.search(r"ENTERADO|JAKINEAN", texto, re.I):
        resultado = "enterado"
    elif re.search(r"RETIRAD[AO]", texto, re.I):
        resultado = "retirado"

    unanimidad = bool(re.search(r"UNANIMIDAD|AHO BATEZ", texto, re.I))

    partidos: dict[str, dict] = {}  # siglas → {votos_favor, votos_contra, abstenciones}

    # VOTOS A FAVOR
    m = re.search(
        r"VOTOS A FAVOR:\s*\d+\s*[-–]\s*(.+?)(?=VOTOS EN CONTRA:|AURKAKO BOTOAK:|ABSTENCIONES:|ABSTENTZIOAK:|$)",
        texto, re.I)
    if m:
        _acumular_votos(m.group(1), "favor", partidos)

    # VOTOS EN CONTRA
    m = re.search(
        r"VOTOS EN CONTRA:\s*\d+\s*[-–]\s*(.+?)(?=ABSTENCIONES:|ABSTENTZIOAK:|$)",
        texto, re.I)
    if m:
        _acumular_votos(m.group(1), "contra", partidos)

    # ABSTENCIONES (con o sin desglose por partido)
    m_abst = re.search(r"ABSTENCIONES:\s*(\d+)", texto, re.I)
    total_abst = int(m_abst.group(1)) if m_abst else 0
    if total_abst > 0:
        # Intentar extraer desglose: "3 – PP" o "(3) PP"
        m_abst_detail = re.search(
            r"ABSTENCIONES:\s*\d+\s*[-–]\s*(.+?)(?:\.|$)", texto, re.I)
        if m_abst_detail:
            _acumular_votos(m_abst_detail.group(1), "abstenciones", partidos)

    if not partidos and resultado == "sin_votacion":
        return None

    return {
        "resultado": resultado,
        "unanimidad": unanimidad,
        "partidos": partidos,
        "total_abstenciones": total_abst,
    }


def _acumular_votos(texto: str, posicion: str, partidos: dict):
    """
    Extrae votos por partido desde texto del tipo:
      '(3) PP, (2) ELKARREKIN DONOSTIA'   → con paréntesis
      'PP, EH BILDU'                        → sin paréntesis (abstenciones simples)
    y acumula en el dict {siglas: {votos_favor, votos_contra, abstenciones}}.
    """
    seen: set[str] = set()

    # Formato con paréntesis: (N) PARTIDO
    for m in re.finditer(
            r"\((\d+)\)\s+([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ/\-\. ]*?)(?=\s*,\s*\(|\s*[·.]|\s*$|\Z)",
            texto):
        votos = int(m.group(1))
        siglas = _normalizar_siglas(m.group(2).strip())
        if siglas and siglas not in seen:
            seen.add(siglas)
            _set_votos(partidos, siglas, posicion, votos)

    # Formato sin paréntesis (abstenciones): "N – PP" o solo "PP"
    if not seen:
        for m in re.finditer(r"([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ/\-\. ]{1,30}?)(?=\s*,|\s*\.|\s*$|\Z)", texto):
            siglas = _normalizar_siglas(m.group(1).strip())
            if siglas and siglas not in seen:
                seen.add(siglas)
                _set_votos(partidos, siglas, posicion, 1)  # sin número exacto


def _normalizar_siglas(s: str) -> str:
    s = s.strip().rstrip(".,")
    # "BILDU" → "EH BILDU" (artefacto del layout bilingüe que parte "EH\nBILDU")
    if s == "BILDU":
        return "EH BILDU"
    return s if len(s) >= 2 else ""


def _set_votos(partidos: dict, siglas: str, posicion: str, votos: int):
    if siglas not in partidos:
        partidos[siglas] = {"votos_favor": 0, "votos_contra": 0, "abstenciones": 0}
    campo = {"favor": "votos_favor", "contra": "votos_contra", "abstenciones": "abstenciones"}[posicion]
    partidos[siglas][campo] += votos


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

Escribe un resumen de 2-3 frases del pleno municipal: qué temas dominaron, qué decisiones clave se tomaron y cuál es su impacto para la ciudadanía. Tono neutro con mirada crítica al impacto social y ambiental. Destaca si hubo decisiones polémicas o rechazadas. Solo el texto, sin JSON, sin markdown, sin introducción.

TEXTO DEL ACTA:
{texto}
"""

SYSTEM_RESUMEN_PUNTO = (
    "Eres un redactor de Acta Civium, publicación ciudadana sobre plenos municipales. "
    "Tu ÚNICA tarea es escribir un resumen de 1-2 frases en castellano explicando "
    "qué se decidió y cuál es el impacto para la ciudadanía. "
    "NUNCA hagas preguntas. NUNCA pidas más información. NUNCA expliques lo que vas a hacer. "
    "Escribe DIRECTAMENTE el resumen como texto plano, sin preámbulos ni markdown. "
    "Si el texto está en euskera o es escaso, infiere del título y el resultado de la votación."
)

PROMPT_RESUMEN_PUNTO = """Genera un resumen de 1-2 frases de este punto del orden del día de un pleno municipal:

Título: {titulo}
Resultado: {resultado}
Texto del acta: {texto}

Escribe solo el resumen, sin introducción ni explicaciones."""


SYSTEM_RESUMEN_PLENO = (
    "Eres un redactor de Acta Civium, publicación ciudadana sobre plenos municipales. "
    "NUNCA hagas preguntas. NUNCA pidas más información. Escribe DIRECTAMENTE el resumen "
    "como texto plano, sin JSON, sin markdown, sin preámbulos."
)


def generar_resumen_pleno(texto: str) -> str | None:
    """Genera un resumen de 2-3 frases del pleno usando los primeros 60K chars del acta.

    Devuelve el texto del resumen o None si Claude no responde.
    La clasificación por punto se hace por separado con generar_resumen_punto().
    """
    texto_recortado = _recortar_texto(texto, max_chars=60_000)
    prompt = PROMPT_RESUMEN_PLENO.format(texto=texto_recortado)
    return _llamar_claude(prompt, system_prompt=SYSTEM_RESUMEN_PLENO, timeout=180)


def generar_resumen_punto(titulo: str, resultado: str, texto: str) -> str | None:
    """Genera resumen corto de un punto individual."""
    texto_recortado = _recortar_texto(texto, max_chars=8_000)
    prompt = PROMPT_RESUMEN_PUNTO.format(
        titulo=titulo, resultado=resultado, texto=texto_recortado
    )
    return _llamar_claude(prompt, system_prompt=SYSTEM_RESUMEN_PUNTO)


def _llamar_claude(prompt: str, system_prompt: str | None = None,
                   timeout: int = 300) -> str | None:
    """Ejecuta Claude CLI de forma no interactiva y devuelve la respuesta.

    El prompt se envía por stdin (no como argumento) para evitar problemas
    con caracteres especiales y límites de longitud en Windows.
    cwd=tempfile.gettempdir() evita que Claude cargue CLAUDE.md del proyecto.
    """
    import tempfile
    # -p sin texto → lee el prompt de stdin
    cmd = [CLAUDE_CMD, "-p", "--output-format", "text"]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            cwd=tempfile.gettempdir(),
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
