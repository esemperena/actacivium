"""
Scraper para el Diario de Sesiones del Pleno del Congreso de los Diputados.
PDFs en: https://www.congreso.es/public_oficiales/L{LEG}/CONG/DS/PL/DSCD-{LEG}-PL-{N}.PDF

No existe API para el Diario de Sesiones — los PDFs son texto real (no escaneado),
sin columnas bilingües, por lo que no se necesita OCR ni recorte de columnas.
"""
import httpx
from pathlib import Path
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential

LEGISLATURA = 15
PDF_URL_TPL = (
    "https://www.congreso.es/public_oficiales/L{leg}/CONG/DS/PL/"
    "DSCD-{leg}-PL-{n}.PDF"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ActaCivium/1.0; +https://actacivium.es)",
    "Accept-Language": "es-ES,es;q=0.9",
}


@dataclass
class ActaRef:
    numero_acta: int   # N en DSCD-15-PL-N (= número de Diario de Sesiones)
    fecha_str: str     # vacío al descubrir; se rellena al parsear el PDF
    tipo: str          # "ordinaria" (solo procesamos sesiones plenarias ordinarias)
    url_pdf: str
    nombre_pdf: str


def obtener_actas_disponibles(
    year: int | None = None,
    desde_n: int = 1,
    max_n: int = 600,
    max_fallos: int = 5,
) -> list[ActaRef]:
    """
    Descubre qué PDFs existen comprobando secuencialmente con HEAD requests.

    Parámetros:
      desde_n    — primer número a comprobar (pasar max_en_bd+1 para operación incremental)
      max_n      — techo de búsqueda
      max_fallos — se detiene si encuentra este nº de 404s consecutivos
      year       — ignorado (los PDFs del Congreso no se organizan por año en la URL)
    """
    if year is not None:
        print(f"  [i] --year ignorado para el Congreso (los PDFs no se organizan por año)")

    actas: list[ActaRef] = []
    fallos_consecutivos = 0

    print(f"  → Comprobando PDFs desde DSCD-{LEGISLATURA}-PL-{desde_n} ...")
    for n in range(desde_n, max_n + 1):
        url = PDF_URL_TPL.format(leg=LEGISLATURA, n=n)
        if _existe_pdf(url):
            fallos_consecutivos = 0
            actas.append(ActaRef(
                numero_acta=n,
                fecha_str="",        # se extrae del PDF durante procesar_acta
                tipo="ordinaria",
                url_pdf=url,
                nombre_pdf=f"DSCD-{LEGISLATURA}-PL-{n}.PDF",
            ))
            print(f"    ✓ DSCD-{LEGISLATURA}-PL-{n}.PDF encontrado")
        else:
            fallos_consecutivos += 1
            if fallos_consecutivos >= max_fallos:
                print(f"    → {max_fallos} 404s consecutivos. Fin de búsqueda en n={n}.")
                break

    return actas


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _existe_pdf(url: str) -> bool:
    """Comprueba existencia del PDF con HEAD request sin descargarlo."""
    try:
        r = httpx.head(url, headers=HEADERS, follow_redirects=True, timeout=15)
        return r.status_code == 200
    except Exception:
        return False


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=15))
def descargar_pdf(url: str, destino: Path) -> bool:
    """Descarga un PDF a disco. Devuelve True si tiene éxito."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream("GET", url, headers=HEADERS, follow_redirects=True, timeout=90) as r:
            r.raise_for_status()
            with open(destino, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"  [!] Error descargando {url}: {e}")
        return False


def fecha_str_a_iso(fecha_str: str) -> str:
    """'26/09/2024' → '2024-09-26'. Devuelve '' si la cadena está vacía."""
    if not fecha_str:
        return ""
    partes = fecha_str.split("/")
    if len(partes) == 3:
        return f"{partes[2]}-{partes[1]}-{partes[0]}"
    return fecha_str
