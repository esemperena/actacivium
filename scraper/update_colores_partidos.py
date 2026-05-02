"""
Actualiza los colores corporativos de los partidos en Supabase.
"""
from db import get_client

# Colores corporativos oficiales
COLORES = {
    # PNV / EAJ-PNV — verde corporativo (Wikidata Q43093)
    "PNV":            "#4AAE4A",
    "EAJ-PNV":        "#4AAE4A",
    # PSE-EE — rojo socialista (PSOE)
    "PSE-EE":         "#E10019",
    "PSE":            "#E10019",
    # EH Bildu — verde-azulado (Wikidata Q1029761)
    "EH BILDU":       "#00AC8E",
    "BILDU":          "#00AC8E",
    # PP — azul corporativo (Wikidata Q185088)
    "PP":             "#1D84CE",
    # Elkarrekin Donostia — morado Podemos/Sumar
    "ELKARREKIN":     "#6A2E8E",
    "ELKARREKIN DONOSTIA": "#6A2E8E",
}


def main():
    client = get_client()
    partidos = client.table("partidos").select("id, siglas, nombre, color_hex").execute().data

    print(f"Partidos en BD: {len(partidos)}\n")

    for p in partidos:
        siglas_up = p["siglas"].upper().strip()
        nuevo_color = None

        # Buscar coincidencia exacta primero, luego parcial
        for key, color in COLORES.items():
            if key in siglas_up or siglas_up in key:
                nuevo_color = color
                break

        actual = p["color_hex"] or "—"
        if nuevo_color and nuevo_color.lower() != actual.lower():
            client.table("partidos").update({"color_hex": nuevo_color}).eq("id", p["id"]).execute()
            print(f"  {p['siglas']:25s}  {actual}  →  {nuevo_color}")
        else:
            print(f"  {p['siglas']:25s}  {actual}  (sin cambios)")


if __name__ == "__main__":
    main()
