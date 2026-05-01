from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def get_municipio_id(nombre: str) -> str:
    res = get_client().table("municipios").select("id").eq("nombre", nombre).single().execute()
    return res.data["id"]


def acta_ya_existe(municipio_id: str, numero_acta: int) -> bool:
    res = (
        get_client()
        .table("plenos")
        .select("id")
        .eq("municipio_id", municipio_id)
        .eq("numero_acta", numero_acta)
        .execute()
    )
    return len(res.data) > 0


def insertar_pleno(datos: dict) -> str:
    res = get_client().table("plenos").insert(datos).execute()
    return res.data[0]["id"]


def actualizar_pleno(pleno_id: str, datos: dict):
    get_client().table("plenos").update(datos).eq("id", pleno_id).execute()


def insertar_punto(datos: dict) -> str:
    res = get_client().table("puntos").insert(datos).execute()
    return res.data[0]["id"]


def insertar_votacion(datos: dict):
    get_client().table("votaciones").insert(datos).execute()


def get_partido_id(municipio_id: str, siglas: str) -> str | None:
    res = (
        get_client()
        .table("partidos")
        .select("id")
        .eq("municipio_id", municipio_id)
        .ilike("siglas", f"%{siglas}%")
        .execute()
    )
    if res.data:
        return res.data[0]["id"]
    return None


def registrar_log(municipio_id: str, pdfs_nuevos: int, pdfs_error: int, duracion: float, detalle: dict):
    get_client().table("scraping_log").insert({
        "municipio_id": municipio_id,
        "pdfs_nuevos": pdfs_nuevos,
        "pdfs_error": pdfs_error,
        "duracion_seg": duracion,
        "detalle": detalle,
    }).execute()
