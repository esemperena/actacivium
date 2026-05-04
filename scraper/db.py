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


def eliminar_pleno(municipio_id: str, numero_acta: int):
    res = (
        get_client()
        .table("plenos")
        .select("id")
        .eq("municipio_id", municipio_id)
        .eq("numero_acta", numero_acta)
        .execute()
    )
    for row in res.data:
        pleno_id = row["id"]
        get_client().table("puntos").delete().eq("pleno_id", pleno_id).execute()
        # votaciones se eliminan en cascada via puntos (punto_id FK)
        get_client().table("plenos").delete().eq("id", pleno_id).execute()


def insertar_pleno(datos: dict) -> str:
    res = get_client().table("plenos").insert(datos).execute()
    return res.data[0]["id"]


def actualizar_pleno(pleno_id: str, datos: dict):
    get_client().table("plenos").update(datos).eq("id", pleno_id).execute()


def insertar_punto(datos: dict) -> str:
    res = get_client().table("puntos").insert(datos).execute()
    return res.data[0]["id"]


def actualizar_punto(punto_id: str, datos: dict):
    get_client().table("puntos").update(datos).eq("id", punto_id).execute()


def insertar_votacion(datos: dict):
    get_client().table("votaciones").insert(datos).execute()


def get_partido_id(municipio_id: str, siglas: str) -> str | None:
    """Matching bidireccional: 'ELKARREKIN DONOSTIA' encuentra 'Elkarrekin'."""
    res = get_client().table("partidos").select("id, siglas").eq("municipio_id", municipio_id).execute()
    siglas_up = siglas.upper().strip()
    for row in res.data:
        db_up = row["siglas"].upper().strip()
        if db_up in siglas_up or siglas_up in db_up:
            return row["id"]
    return None


def insertar_asistencia_bulk(registros: list[dict]):
    if registros:
        get_client().table("asistencia").insert(registros).execute()


def limpiar_asistencia_pleno(pleno_id: str):
    get_client().table("asistencia").delete().eq("pleno_id", pleno_id).execute()


def registrar_log(municipio_id: str, pdfs_nuevos: int, pdfs_error: int, duracion: float, detalle: dict):
    get_client().table("scraping_log").insert({
        "municipio_id": municipio_id,
        "pdfs_nuevos": pdfs_nuevos,
        "pdfs_error": pdfs_error,
        "duracion_seg": duracion,
        "detalle": detalle,
    }).execute()
