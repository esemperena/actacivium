"""
Extrae texto y datos estructurados del Diario de Sesiones del Pleno
del Congreso de los Diputados.

Estructura real del PDF (verificada con DSCD-15-PL-183.PDF):

  Pág. 1 — Portada: ORDEN DEL DÍA con items "—" agrupados por categoría.
            Solo los items con debate tienen "—" aquí; los votados en bloque
            (proposiciones, mociones) solo aparecen como sección con nº de página.

  Págs. 2-N — SUMARIO: lista completa de todos los items con expediente y,
               para cada item con votación, resultado compacto:
               "Sometida a votación la iniciativa de referencia, se aprueba/rechaza
               por X votos a favor[, Y en contra][, Z abstenciones]."

  Resto — Cuerpo de la sesión. Al final: bloques de votación con:
           "Efectuada la votación, dio el siguiente resultado:
            votos emitidos, NNN; a favor, NNN; en contra, NNN[; abstenciones, NNN]."
           seguido de: "La señora PRESIDENTA: Queda aprobada/rechazada."

Estrategia de parsing:
  - Puntos del orden del día → extraídos del SUMARIO (tiene TODOS los items)
  - Votaciones               → SUMARIO (compacto) como fuente primaria;
                               body "Efectuada la votación" como fuente secundaria
  - No hay desglose por grupo en los resultados del DS ordinario
"""
import re
import subprocess
import tempfile
import pdfplumber
from pathlib import Path
from config import CLAUDE_CMD, PDF_MAX_PAGES_FOR_SUMMARY

MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
}

# Em dash (U+2014) que usa el Congreso para bullets de items
EM_DASH = "—"
# Non-breaking hyphen (U+2011) que aparece en referencias (número 92‑1)
NB_HYPHEN = "‑"


# ── Extracción de texto ───────────────────────────────────────────────────────

def extraer_texto(pdf_path: Path) -> str:
    """Extrae todo el texto del PDF. DS del Congreso = columna única."""
    partes = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=2, y_tolerance=2)
            if texto:
                partes.append(texto)
    return _limpiar_texto("\n".join(partes))


def extraer_texto_castellano(pdf_path: Path) -> str:
    """Alias — el DS del Congreso es monolingüe."""
    return extraer_texto(pdf_path)


def _limpiar_texto(texto: str) -> str:
    # Encabezado repetido en cada página
    texto = re.sub(
        r"DIARIO DE SESIONES DEL CONGRESO DE LOS DIPUTADOS\nPLENO Y DIPUTACIÓN PERMANENTE\n"
        r"Núm\. \d+ \d+ de \w+ de \d{4} Pág\. \d+\n",
        "", texto,
    )
    texto = re.sub(r"\d{3}-LP-\d{2}-DCSD\n:evc\n?", "", texto)   # código interno
    texto = re.sub(r"cve:[^\n]+\n?", "", texto)
    texto = texto.replace(NB_HYPHEN, "-")                           # normalizar guion no separable
    texto = re.sub(r"\n{4,}", "\n\n\n", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()


# ── Metadata ──────────────────────────────────────────────────────────────────

def extraer_metadatos(texto: str) -> dict:
    """
    Extrae cabecera del DS del Congreso.
    Devuelve: numero_ds, numero_sesion, fecha_str, fecha_iso,
              tipo_sesion, presidenta_nombre, legislatura.
    """
    meta: dict = {}

    # Número del Diario de Sesiones: "Núm. 183"
    m = re.search(r"XV LEGISLATURA\s+N[uú]m\.\s+(\d+)", texto[:500])
    if not m:
        m = re.search(r"\bN[uú]m\.\s+(\d+)", texto[:500])
    if m:
        meta["numero_ds"] = int(m.group(1))

    # Número de sesión plenaria: "Sesión plenaria núm. 177"
    m = re.search(r"Sesi[oó]n plenaria n[uú]m\.\s*(\d+)", texto, re.I)
    if m:
        meta["numero_sesion"] = int(m.group(1))

    # Fecha: "celebrada el jueves 30 de abril de 2026"
    m = re.search(
        r"celebrada el\s+(?:\w+\s+)?(\d{1,2}) de (\w+) de (\d{4})",
        texto, re.I,
    )
    if m:
        dia, mes_str, año = m.group(1), m.group(2).lower(), m.group(3)
        mes = MESES.get(mes_str, "01")
        meta["fecha_str"] = f"{dia.zfill(2)}/{mes}/{año}"
        meta["fecha_iso"] = f"{año}-{mes}-{dia.zfill(2)}"

    # Presidenta (nombre puede estar partido en dos líneas)
    m = re.search(
        r"PRESIDENCIA DE LA EXCM[AO]\.? SR[AO]\.? D\.?[Aª]\.?\s+(.+?)(?:\n|\Z)",
        texto, re.I,
    )
    if m:
        # Puede seguir en la siguiente línea (apellidos)
        nombre = m.group(1).strip()
        pos = m.end()
        siguiente = re.match(r"([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]+)(?:\n|Sesión)", texto[pos:])
        if siguiente:
            nombre = (nombre + " " + siguiente.group(1)).strip()
        meta["presidenta_nombre"] = re.sub(r"\s+", " ", nombre)

    meta["tipo_sesion"] = "ordinaria"
    if re.search(r"sesi[oó]n\s+extraordinaria", texto[:3000], re.I):
        meta["tipo_sesion"] = "extraordinaria"

    return meta


# ── Asistencia ────────────────────────────────────────────────────────────────
# El DS del Congreso no lista asistencia individual — se devuelven vacíos.

def extraer_asistentes(texto: str) -> tuple[list[str], list[str]]:
    return [], []


def extraer_asistentes_con_partido(texto: str) -> list[dict]:
    return []


# ── Helpers de sección ───────────────────────────────────────────────────────

# Cabeceras de sección → tipo de iniciativa
_SECCIONES_TIPO = [
    (r"convalidaci[oó]n o derogaci[oó]n de reales decretos",  "aprobacion_definitiva"),
    (r"debates? de totalidad",                                  "aprobacion_inicial"),
    (r"proyectos? de ley",                                      "aprobacion_definitiva"),
    (r"dictamen",                                               "aprobacion_definitiva"),
    (r"proposiciones? no de ley",                               "mocion"),
    (r"mociones? consecuencia de interpelaciones?",             "mocion"),
    (r"interpelaciones? urgentes?",                             "interpelacion"),
    (r"preguntas? con respuesta oral",                          "pregunta_oral"),
    (r"preguntas? con respuesta escrita",                       "pregunta_escrita"),
]


def _tipo_de_linea(linea: str) -> str | None:
    """Devuelve el tipo si la línea es una cabecera de sección, None si no lo es."""
    clean = re.sub(r"\.\s*\(Votaci[oó]n\)", "", linea, flags=re.I)
    clean = re.sub(r"\.{3,}\s*\d*\s*$", "", clean).strip()
    for patron, tipo in _SECCIONES_TIPO:
        if re.search(patron, clean, re.I):
            return tipo
    return None


# ── Puntos del SUMARIO ────────────────────────────────────────────────────────

def extraer_puntos_sumario(texto: str) -> list[dict]:
    """
    Extrae los puntos del orden del día desde el SUMARIO del DS (páginas 2-N).

    El SUMARIO lista los mismos items dos veces para iniciativas debatidas+votadas:
    una vez en la sección de debate y otra en la sección de votación.
    Se deduplicaa por número de expediente; si no hay expediente, por título.

    Devuelve lista de {numero, titulo, expediente, tipo_seccion, grupo_proponente_raw}.
    """
    items = _extraer_items_sumario(texto)

    # Deduplicar: mantener la primera aparición, añadir voto si la segunda lo tiene
    vistos_exp: dict[str, dict] = {}   # expediente → item
    vistos_tit: dict[str, dict] = {}   # titulo_norm → item
    resultado: list[dict] = []

    for item in items:
        exp = item.get("expediente")
        tit_norm = re.sub(r"\s+", " ", item["titulo"].lower()[:60])

        if exp and exp in vistos_exp:
            continue   # duplicado por expediente → ignorar
        if not exp and tit_norm in vistos_tit:
            continue   # duplicado por título → ignorar

        item["numero"] = len(resultado) + 1
        resultado.append(item)
        if exp:
            vistos_exp[exp] = item
        else:
            vistos_tit[tit_norm] = item

    return resultado


def _extraer_items_sumario(texto: str) -> list[dict]:
    """
    Divide el bloque SUMARIO por bullets '—' y parsea cada bloque.
    Cada bloque puede abarcar varias líneas.
    """
    m_ini = re.search(r"\bSUMARIO\b", texto, re.I)
    if not m_ini:
        m_ini = re.search(r"\bORDEN DEL D[IÍ]A\b", texto, re.I)
    if not m_ini:
        return []

    m_fin = re.search(r"\bSESI[ÓO]N PLENARIA\b", texto[m_ini.end():], re.I)
    fin = m_ini.end() + (m_fin.start() if m_fin else 15_000)
    bloque = texto[m_ini.end(): fin]

    # Dividir por em-dash al inicio de línea (bullet de item)
    # Usamos un patrón que preserva el separador para poder rastrear sección
    partes = re.split(r"(?=\n[—]\s)", bloque)

    items: list[dict] = []
    tipo_seccion_actual = "otro"
    # Los encabezados de sección del ítem N aparecen al FINAL del bloque del ítem N-1
    # (porque el split deja cada bullet al inicio de su parte y la descripción + el
    # encabezado siguiente al final).  Separamos las líneas pre-bullet (aplicables
    # al ítem actual) de las post-bullet (aplicables al ítem siguiente).
    pendiente_tipo: str | None = None   # tipo detectado en la parte anterior

    for parte in partes:
        lineas = parte.strip().split("\n")

        # Aplicar el tipo detectado en el bloque anterior (encabezado de sección
        # que precede al bullet de ESTA parte)
        if pendiente_tipo is not None:
            tipo_seccion_actual = pendiente_tipo
            pendiente_tipo = None

        # Separar líneas pre-bullet y post-bullet
        pre_bullet: list[str] = []
        post_bullet: list[str] = []
        en_item = False
        for linea in lineas:
            if linea.strip().startswith("—"):
                en_item = True
            (post_bullet if en_item else pre_bullet).append(linea)

        # Actualizar tipo desde encabezados que preceden al bullet en esta misma parte
        for linea in pre_bullet:
            t = _tipo_de_linea(linea.strip())
            if t:
                tipo_seccion_actual = t

        # ¿Esta parte contiene un item?
        bloque_item = " ".join(l.strip() for l in lineas if l.strip())
        m_item = re.search(r"[—]\s+(.+)", bloque_item)

        # Detectar encabezado de sección en las líneas DESPUÉS del bullet
        # (pertenece al siguiente ítem)
        for linea in post_bullet:
            t = _tipo_de_linea(linea.strip())
            if t:
                pendiente_tipo = t

        if not m_item:
            continue

        texto_item = m_item.group(1)

        # Extraer expediente — "Número de expediente XXXXXX" puede tener espacios/saltos
        # Lo buscamos en el bloque_item original (sin join) para tener el texto sin colapsar
        bloque_orig = "\n".join(lineas)
        expediente = _buscar_expediente(bloque_orig)

        # Título: parte antes del expediente (o antes de las referencias BOCG)
        titulo = _extraer_titulo_del_bloque(texto_item, expediente)
        titulo = _limpiar_titulo(titulo)
        if len(titulo) < 5:
            continue

        grupo_raw = _extraer_grupo_del_titulo(titulo)

        items.append({
            "titulo": titulo,
            "expediente": expediente,
            "tipo_seccion": tipo_seccion_actual,
            "grupo_proponente_raw": grupo_raw,
        })

    return items


def _buscar_expediente(texto: str) -> str | None:
    """Busca 'Número de expediente NNN/NNNNNN' tolerando saltos de línea internos."""
    # El texto puede tener "Número de\nexpediente 162/000745" o
    # "(Número de expediente\n130/000040)"
    m = re.search(
        r"N[uú]mero\s+de\s+expediente\s+([\d]+/[\d]+)",
        texto, re.I,
    )
    if m:
        return m.group(1)
    # Fallback: patrón desnudo NNN/NNNNNN
    m = re.search(r"\b(\d{3}/\d{6})\b", texto)
    return m.group(1) if m else None


def _extraer_titulo_del_bloque(texto_item: str, expediente: str | None) -> str:
    """Extrae el título del item, quitando la referencia de expediente y las puntos de relleno."""
    # Quitar desde "(Número de expediente" en adelante
    titulo = re.sub(r"\(N[uú]mero\s+de\s+expediente.*", "", texto_item, flags=re.I | re.DOTALL)
    # Si hay expediente como número desnudo, quitar desde él
    if expediente:
        titulo = titulo.split(expediente)[0]
    # Quitar referencia BOCG completa: «BOCG...», serie X, número N-N, de DD de MES de YYYY.
    # [^(]* barre también el `, serie A, número 92-1, de 13 de abril de 2026.` posterior
    titulo = re.sub(r"\.?\s*«BOCG[^»]*»[^(]*", "", titulo, flags=re.I)
    titulo = re.sub(r"\(B\.O\.E\.[^)]+\)", "", titulo)
    # Quitar puntos de relleno y número de página al final
    titulo = re.sub(r"[\s.]{3,}\d*\s*$", "", titulo)
    # Quitar "Sometida a votación" si quedó pegado (no debería con el split, pero por si acaso)
    titulo = re.sub(r"Sometida a votaci[oó]n.*", "", titulo, flags=re.I | re.DOTALL)
    return titulo.strip(" .,")


def _limpiar_titulo(titulo: str) -> str:
    titulo = re.sub(r"\s+", " ", titulo)
    titulo = titulo.replace(NB_HYPHEN, "-")
    return titulo.strip(" .,")


def _extraer_grupo_del_titulo(titulo: str) -> str | None:
    m = re.match(
        r"Del Grupo Parlamentar(?:io|i)\s+(.+?)(?:,\s*(?:relativa|sobre|por|acerca)|\.|\Z)",
        titulo, re.I,
    )
    return m.group(1).strip() if m else None


# ── Votaciones ────────────────────────────────────────────────────────────────

def extraer_votaciones_por_punto(texto: str) -> dict[int, dict]:
    """
    Extrae resultados de votación asociados a cada punto.

    Fuente primaria — SUMARIO: "Sometida a votación..., se aprueba/rechaza por X votos..."
    Los resultados del SUMARIO van ligados a los items; se asignan al número de punto
    que les corresponde según la lista deduplicada de extraer_puntos_sumario.

    Fuente secundaria — cuerpo del DS: "Efectuada la votación, dio el siguiente resultado:"
    """
    result: dict[int, dict] = {}

    # Obtener lista de puntos deduplicados para saber la numeración correcta
    puntos = extraer_puntos_sumario(texto)
    exp_a_num = {p["expediente"]: p["numero"] for p in puntos if p.get("expediente")}

    # ── Fuente 1: SUMARIO ─────────────────────────────────────────────────────
    m_ini = re.search(r"\bSUMARIO\b", texto, re.I)

    if m_ini:
        # Buscar "SESIÓN PLENARIA" DESPUÉS del SUMARIO (no desde el inicio,
        # donde aparece en la cabecera antes del SUMARIO)
        m_fin_body = re.search(r"\bSESI[ÓO]N PLENARIA\b", texto[m_ini.end():], re.I)
        fin_sumario = m_ini.end() + (m_fin_body.start() if m_fin_body else 15_000)
        bloque = texto[m_ini.end(): fin_sumario]
        _parsear_votos_sumario(bloque, puntos, exp_a_num, result)

    # ── Fuente 2: cuerpo del DS (complementa o sustituye al SUMARIO) ─────────
    if not result:
        _parsear_votos_cuerpo(texto, result)

    return result


def _parsear_votos_sumario(bloque: str, puntos: list, exp_a_num: dict, result: dict):
    """
    Busca 'Sometida a votación' en el SUMARIO y asocia cada resultado al punto correcto
    usando el expediente como clave.
    """
    # Dividir por bullets igual que en _extraer_items_sumario
    partes = re.split(r"(?=\n[—]\s)", bloque)

    for parte in partes:
        bloque_orig = "\n".join(l.strip() for l in parte.strip().split("\n") if l.strip())
        bloque_flat = " ".join(bloque_orig.split())

        # ¿Tiene resultado de votación?
        datos = _parsear_resultado_sumario(bloque_flat)
        if not datos:
            continue

        # ¿Qué expediente tiene este bloque?
        exp = _buscar_expediente(bloque_orig)
        if exp and exp in exp_a_num:
            num = exp_a_num[exp]
            if num not in result:
                result[num] = datos
        else:
            # Sin expediente: asignar al primer punto sin resultado que tenga
            # la misma sección (heurística)
            for p in puntos:
                if p["numero"] not in result:
                    result[p["numero"]] = datos
                    break


def _parsear_resultado_sumario(texto: str) -> dict | None:
    """
    Extrae resultado de la forma:
      "se aprueba/rechaza por X votos a favor[, Y en contra][, Z abstenciones]"
    o "son aprobados todos" (sin números).
    """
    texto_plano = " ".join(texto.split())

    # Patrón con números
    m = re.search(
        r"se\s+(aprueba|rechaza|aprueban|rechazan|convalida|deroga)\b[^.]*"
        r"por\s+(\d+)\s+votos?\s+a\s+favor"
        r"(?:[,\sy]+(\d+)[,\s]+en\s+contra)?"
        r"(?:[,\sy]+(\d+)\s+abstenciones?)?",
        texto_plano, re.I,
    )
    if m:
        accion = m.group(1).lower()
        favor = int(m.group(2))
        contra = int(m.group(3)) if m.group(3) else 0
        abstenciones = int(m.group(4)) if m.group(4) else 0

        resultado = "aprobado" if re.search(r"aprueba|aprueban|convalida", accion) else "rechazado"
        unanimidad = (contra == 0 and abstenciones == 0) or None

        return {
            "resultado": resultado,
            "unanimidad": unanimidad,
            "partidos": {},
            "total_favor": favor,
            "total_contra": contra,
            "total_abstenciones": abstenciones,
        }

    # "son aprobados todos" / "son rechazados todos" (sin números)
    if re.search(r"son aprobados? todos?", texto_plano, re.I):
        return {"resultado": "aprobado", "unanimidad": None, "partidos": {},
                "total_favor": 0, "total_contra": 0, "total_abstenciones": 0}

    return None


def _parsear_votos_cuerpo(texto: str, result: dict):
    """
    Fallback: parsea "Efectuada la votación, dio el siguiente resultado:
    votos emitidos, N; a favor, N; en contra, N[; abstenciones, N]."
    seguido de "Queda aprobada/rechazada/convalidado".
    Asocia al primer punto sin resultado en orden.
    """
    patron = re.compile(
        r"Efectuada la votaci[oó]n,\s+dio el siguiente resultado:\s*"
        r"votos? emitidos?,\s*(\d+);\s*a favor,\s*(\d+);\s*en contra,\s*(\d+)"
        r"(?:;\s*abstenciones?,\s*(\d+))?",
        re.I,
    )
    siguiente_num = 1
    for m in patron.finditer(texto):
        favor = int(m.group(2))
        contra = int(m.group(3))
        abstenciones = int(m.group(4)) if m.group(4) else 0

        # Leer resultado de los siguientes ~200 chars
        pos_fin = m.end()
        fragmento_post = texto[pos_fin: pos_fin + 200]
        if re.search(r"Queda\s+(aprobad[ao]|convalidado)", fragmento_post, re.I):
            resultado = "aprobado"
        elif re.search(r"Queda\s+(rechazad[ao]|derogado)", fragmento_post, re.I):
            resultado = "rechazado"
        elif favor > contra:
            resultado = "aprobado"
        else:
            resultado = "rechazado"

        unanimidad = (contra == 0 and abstenciones == 0) or None

        # Asignar al siguiente número sin resultado
        while siguiente_num in result:
            siguiente_num += 1
        result[siguiente_num] = {
            "resultado": resultado,
            "unanimidad": unanimidad,
            "partidos": {},
            "total_favor": favor,
            "total_contra": contra,
            "total_abstenciones": abstenciones,
        }
        siguiente_num += 1


# ── Clasificación temática ────────────────────────────────────────────────────

CATEGORIAS_KEYWORDS: dict[str, list[str]] = {
    "vivienda": [
        "vivienda", "alquiler", "hipoteca", "arrendamiento", "desahucio",
        "acceso a la vivienda", "habitacional",
    ],
    "hacienda": [
        "presupuesto", "ley de presupuestos", "impuesto", "tribut", "deuda",
        "déficit", "gasto público", "financiación", "fiscal",
    ],
    "medio_ambiente": [
        "medio ambiente", "cambio climático", "emisiones", "residuos",
        "biodiversidad", "energía renovable", "sostenibilidad", "contaminación",
        "agua", "parques nacionales", "costas",
    ],
    "servicios_sociales": [
        "servicios sociales", "dependencia", "pobreza", "exclusión social",
        "prestaciones", "pensiones", "ingreso mínimo", "bienestar",
    ],
    "movilidad": [
        "transporte", "tráfico", "infraestructuras", "tren", "cercanías",
        "autopista", "carretera", "puertos", "aeropuerto",
    ],
    "educacion": [
        "educación", "enseñanza", "escuela", "universidad", "becas",
        "formación profesional", "investigación", "ciencia",
    ],
    "sanidad": [
        "sanidad", "salud", "hospital", "medicamento", "farmacia",
        "sistema nacional de salud", "pandemia", "vacuna", "aborto",
    ],
    "derechos": [
        "derechos", "igualdad", "género", "violencia de género", "lgtbi",
        "discriminación", "mujer", "constitución", "libertad", "democracia",
    ],
    "gobernanza": [
        "gobierno", "congreso", "senado", "estatuto", "autonomía",
        "unión europea", "exterior", "reforma constitucional", "decreto",
    ],
    "seguridad": [
        "seguridad", "defensa", "fuerzas armadas", "policía", "terrorismo",
        "guardia civil",
    ],
    "cultura": [
        "cultura", "patrimonio", "deporte", "turismo", "lenguas", "arte",
    ],
    "urbanismo": [
        "urbanismo", "ordenación del territorio", "suelo", "costas",
        "puertos", "infraestructuras hídricas",
    ],
}


def clasificar_categoria(titulo: str, texto: str = "") -> str:
    contenido = (titulo + " " + texto).lower()
    for categoria, keywords in CATEGORIAS_KEYWORDS.items():
        if any(kw in contenido for kw in keywords):
            return categoria
    return "otro"


def clasificar_tipo(titulo: str) -> str:
    """
    Para el Congreso, el tipo ya viene indicado por la sección del SUMARIO.
    Esta función sirve como fallback cuando solo se tiene el título.
    """
    t = titulo.lower()
    if re.search(r"proyecto de ley|dictamen|reforma constitucional|real decreto[- ]ley", t):
        return "aprobacion_definitiva"
    if re.search(r"proposici[oó]n de ley", t):
        return "proposicion_normativa"
    if re.search(r"proposici[oó]n no de ley|del grupo parlamentario", t):
        return "mocion"
    if re.search(r"moci[oó]n consecuencia", t):
        return "mocion"
    if re.search(r"interpelaci[oó]n", t):
        return "interpelacion"
    if re.search(r"pregunta oral", t):
        return "pregunta_oral"
    if re.search(r"pregunta escrita", t):
        return "pregunta_escrita"
    if re.search(r"informe|comunicaci[oó]n|comparecencia", t):
        return "dar_cuenta"
    return "otro"


def clasificar_comision(titulo: str) -> str:
    return "pleno"


# ── Grupo proponente ──────────────────────────────────────────────────────────

def extraer_grupo_proponente_raw(titulo: str, texto: str = "") -> str | None:
    """Extrae el grupo proponente. Para el Congreso suele estar en el propio título."""
    m = re.match(
        r"Del Grupo Parlamentar(?:io|i)\s+(.+?)(?:,\s*(?:relativa|sobre|por|acerca)|\.|\Z)",
        titulo or "", re.I,
    )
    if m:
        return m.group(1).strip()
    # Buscar en fragmento del cuerpo
    m = re.search(
        r"(?:presentada|formulada|propuesta)\s+por\s+el\s+(?:Grupo\s+Parlamentar[^\n,]{2,50})",
        (texto or "")[:600], re.I,
    )
    if m:
        grupo = re.sub(r"^(presentada|formulada|propuesta)\s+por\s+el\s+", "", m.group(0), flags=re.I)
        return grupo.strip()[:80]
    return None


# ── Relevancia social ─────────────────────────────────────────────────────────

_CATEGORIA_RELEVANCIA = {
    "vivienda": 2, "servicios_sociales": 2, "derechos": 2,
    "medio_ambiente": 2, "educacion": 2, "sanidad": 2,
    "movilidad": 1, "hacienda": 1, "seguridad": 1, "cultura": 1, "gobernanza": 1,
}

_TIPO_RELEVANCIA = {
    "mocion": 1, "proposicion_normativa": 2, "aprobacion_definitiva": 2,
    "aprobacion_inicial": 1, "declaracion_institucional": 1,
}

_RELEVANCIA_KEYWORDS = {
    2: ["vivienda", "alquiler", "desahucio", "pensiones", "ingreso mínimo",
        "cambio climático", "servicios sociales", "violencia de género",
        "igualdad", "sanidad", "educación", "becas", "pobreza", "aborto"],
    1: ["impuesto", "tasa", "presupuesto", "financiación", "defensa",
        "infraestructura", "transporte", "decreto", "convenio"],
}


def calcular_relevancia_social(
    titulo: str,
    *,
    categoria: str | None = None,
    tipo: str | None = None,
    resultado: str | None = None,
    unanimidad: bool | None = None,
    resumen: str = "",
    texto: str = "",
) -> int:
    contenido = " ".join(p for p in [titulo, resumen, texto] if p).lower()
    score = 1
    if categoria:
        score += _CATEGORIA_RELEVANCIA.get(categoria, 0)
    if tipo:
        score += _TIPO_RELEVANCIA.get(tipo, 0)
    for bonus, keywords in _RELEVANCIA_KEYWORDS.items():
        if any(kw in contenido for kw in keywords):
            score += bonus
            break
    if resultado == "rechazado":
        score += 1
    if unanimidad is False:
        score += 1
    if tipo in ("dar_cuenta", "otro") and categoria in ("gobernanza", "otro"):
        score = min(score, 2)
    return max(1, min(5, score))


# ── Fragmento de texto por punto ──────────────────────────────────────────────

def _extraer_fragmento(texto: str, numero: int) -> str:
    """
    Para el Congreso, el extracto más rico es el SUMARIO.
    Busca el bloque del n-ésimo item en el SUMARIO.
    """
    m_ini = re.search(r"\bSUMARIO\b", texto, re.I)
    if not m_ini:
        return ""

    # Buscar SESIÓN PLENARIA después del SUMARIO (la que está en cabecera no vale)
    m_fin_body = re.search(r"\bSESI[ÓO]N PLENARIA\b", texto[m_ini.end():], re.I)
    sumario = texto[m_ini.end(): m_ini.end() + (m_fin_body.start() if m_fin_body else 15_000)]

    # Encontrar el n-ésimo item (—) en el SUMARIO
    items = list(re.finditer(r"(?:^|\n)[—\-—]\s+", sumario, re.MULTILINE))
    if not items or numero > len(items):
        return ""

    inicio = items[numero - 1].start()
    fin = items[numero].start() if numero < len(items) else inicio + 3000
    return sumario[inicio:fin][:3000]


# ── Resúmenes con Claude CLI ──────────────────────────────────────────────────

PROMPT_RESUMEN_PLENO = """Eres el redactor de Acta Civium, publicación ciudadana sobre el Congreso de los Diputados.

Escribe un resumen de 2-3 frases del pleno: qué temas dominaron, qué decisiones clave se tomaron y cuál es su impacto para la ciudadanía. Tono neutro con mirada crítica al impacto social y ambiental. Destaca si hubo decisiones polémicas o rechazadas. Solo el texto, sin JSON, sin markdown, sin introducción.

TEXTO DEL DIARIO DE SESIONES:
{texto}
"""

SYSTEM_RESUMEN_PUNTO = (
    "Eres un redactor de Acta Civium, publicación ciudadana sobre el Congreso de los Diputados. "
    "Escribe un resumen de 1-2 frases en castellano explicando qué se decidió y cuál es el impacto "
    "para la ciudadanía. NUNCA hagas preguntas. Escribe DIRECTAMENTE el resumen como texto plano."
)

PROMPT_RESUMEN_PUNTO = """Genera un resumen de 1-2 frases de este punto del orden del día del pleno del Congreso:

Título: {titulo}
Resultado: {resultado}
Texto del Diario de Sesiones: {texto}

Escribe solo el resumen, sin introducción."""

SYSTEM_TITULO_PUNTO = (
    "Eres un redactor de Acta Civium, publicación ciudadana sobre el Congreso de los Diputados. "
    "Reescribe el título de un punto del orden del día para que sea una frase completa, clara "
    "y comprensible. Máximo 85 caracteres. Sin puntos suspensivos. Solo el título, sin comillas."
)

PROMPT_TITULO_PUNTO = """Reescribe este título para que sea claro y comprensible:

Título original: {titulo}
Resultado: {resultado}
Fragmento: {texto}

Solo el título reescrito, máximo 85 caracteres."""

SYSTEM_RESUMEN_PLENO = (
    "Eres un redactor de Acta Civium. Escribe DIRECTAMENTE el resumen como texto plano, "
    "sin JSON, sin markdown, sin preámbulos."
)


def generar_resumen_pleno(texto: str) -> str | None:
    texto_recortado = _recortar_texto(texto, max_chars=60_000)
    return _llamar_claude(
        PROMPT_RESUMEN_PLENO.format(texto=texto_recortado),
        system_prompt=SYSTEM_RESUMEN_PLENO, timeout=180,
    )


def generar_resumen_punto(titulo: str, resultado: str, texto: str) -> str | None:
    return _llamar_claude(
        PROMPT_RESUMEN_PUNTO.format(
            titulo=titulo, resultado=resultado,
            texto=_recortar_texto(texto, 8_000),
        ),
        system_prompt=SYSTEM_RESUMEN_PUNTO,
    )


def _titulo_necesita_reescritura(titulo: str) -> bool:
    if not titulo or len(titulo.split()) < 4:
        return True
    if len(titulo) > 85:
        return True
    if re.search(r"\b(el|la|de|del|por|en|con|a|al|un|una|para|que|y|o)\s*$", titulo, re.I):
        return True
    if titulo[0].islower():
        return True
    return False


def generar_titulo_punto(titulo: str, resultado: str, texto: str) -> str | None:
    resultado_ia = _llamar_claude(
        PROMPT_TITULO_PUNTO.format(
            titulo=titulo, resultado=resultado,
            texto=_recortar_texto(texto, 3_000),
        ),
        system_prompt=SYSTEM_TITULO_PUNTO,
    )
    if resultado_ia:
        limpio = resultado_ia.strip().strip('"').strip("'")
        if len(limpio) > 90:
            limpio = limpio[:87].rsplit(" ", 1)[0] + "…"
        return limpio
    return None


def _llamar_claude(prompt: str, system_prompt: str | None = None,
                   timeout: int = 300) -> str | None:
    cmd = [CLAUDE_CMD, "-p", "--output-format", "text"]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]
    try:
        result = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", cwd=tempfile.gettempdir(),
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _recortar_texto(texto: str, max_chars: int) -> str:
    if len(texto) <= max_chars:
        return texto
    corte = texto.rfind("\n", 0, max_chars)
    return texto[: corte if corte > 0 else max_chars]
