"""
Scraper para las actas de plenos del Ayuntamiento de San Sebastián (Donostia).
Web: https://www.donostia.eus (IBM Lotus Notes / Domino — HTML estático)
"""
import re
import httpx
import time
from pathlib import Path
from dataclasses import dataclass
from scrapling import Fetcher
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://www.donostia.eus"
LISTING_URL = (
    "https://www.donostia.eus/secretaria/AsuntosPleno.nsf"
    "/fwListadoAnio?ReadForm&idioma=cas&id=C511345"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ActaCivium/1.0; +https://actacivium.es)",
    "Accept-Language": "es-ES,es;q=0.9",
}


@dataclass
class ActaRef:
    numero_acta: int
    fecha_str: str
    tipo: str        # "ordinaria" | "extraordinaria"
    url_pdf: str
    nombre_pdf: str


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch(url: str) -> str:
    """Fetcher HTTP ligero con reintentos automáticos."""
    fetcher = Fetcher(auto_match=False)
    page = fetcher.get(url, headers=HEADERS, follow_redirects=True)
    return page.html_content


def obtener_actas_disponibles() -> list[ActaRef]:
    """
    Parsea la página de listado de actas de Donostia y devuelve
    todas las referencias a PDFs disponibles.
    """
    html = _fetch(LISTING_URL)

    fetcher = Fetcher(auto_match=False)
    # Scrapling puede parsear HTML directamente desde string
    from scrapling import HTMLParser
    page = HTMLParser(html)

    actas: list[ActaRef] = []

    # Los links a PDFs siguen el patrón $file/acYYYYMMDD-XX...pdf
    for link in page.css("a[href*='$file']"):
        href = link.attrib.get("href", "")
        if not href.lower().endswith(".pdf"):
            continue

        url_pdf = href if href.startswith("http") else BASE_URL + href
        nombre_pdf = Path(href).name

        info = _parsear_nombre_pdf(nombre_pdf, link.text or "")
        if info:
            actas.append(ActaRef(
                numero_acta=info["numero"],
                fecha_str=info["fecha_str"],
                tipo=info["tipo"],
                url_pdf=url_pdf,
                nombre_pdf=nombre_pdf,
            ))

    return actas


def _parsear_nombre_pdf(nombre: str, texto_link: str) -> dict | None:
    """
    Extrae número de acta, fecha y tipo del nombre del archivo o del texto del enlace.
    Ejemplo de nombre: ac20251030-39 ZD_sin.pdf
    Ejemplo de texto:  AKTA 39 ACTA 39 2025EKO URRIAK 30 30 DE OCTUBRE DE 2025
    """
    # Intentar desde el nombre del archivo: acYYYYMMDD-NN
    m = re.search(r"ac(\d{4})(\d{2})(\d{2})[_\-\s]*(\d+)", nombre, re.IGNORECASE)
    if m:
        año, mes, dia, num = m.groups()
        fecha_str = f"{dia}/{mes}/{año}"
        tipo = "extraordinaria" if "ex" in nombre.lower() else "ordinaria"
        return {"numero": int(num), "fecha_str": fecha_str, "tipo": tipo}

    # Fallback: extraer desde el texto del enlace
    m = re.search(r"ACTA\s+(\d+).*?(\d{1,2}) DE (\w+) DE (\d{4})", texto_link, re.IGNORECASE)
    if m:
        num, dia, mes_str, año = m.groups()
        mes = _mes_a_numero(mes_str)
        fecha_str = f"{dia.zfill(2)}/{mes.zfill(2)}/{año}"
        return {"numero": int(num), "fecha_str": fecha_str, "tipo": "ordinaria"}

    return None


MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
}


def _mes_a_numero(mes_str: str) -> str:
    return MESES.get(mes_str.lower(), "01")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=15))
def descargar_pdf(url: str, destino: Path) -> bool:
    """Descarga un PDF a disco. Devuelve True si tiene éxito."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream("GET", url, headers=HEADERS, follow_redirects=True, timeout=60) as r:
            r.raise_for_status()
            with open(destino, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"  [!] Error descargando {url}: {e}")
        return False


def fecha_str_a_iso(fecha_str: str) -> str:
    """'26/09/2024' → '2024-09-26'"""
    partes = fecha_str.split("/")
    if len(partes) == 3:
        return f"{partes[2]}-{partes[1]}-{partes[0]}"
    return fecha_str
