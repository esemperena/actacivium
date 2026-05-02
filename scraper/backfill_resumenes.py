"""
Genera resumen_ia para puntos que no lo tienen, usando Claude CLI.

Uso:
  python backfill_resumenes.py           # todos los puntos sin resumen
  python backfill_resumenes.py --pleno 39  # solo puntos del acta 39
"""
import argparse
import time
from db import get_client
from pdf_processor import generar_resumen_punto, PROMPT_RESUMEN_PLENO
import re, json, subprocess
from config import CLAUDE_CMD


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pleno", type=int, help="Número de acta a procesar")
    args = parser.parse_args()

    client = get_client()

    # Obtener plenos procesados
    q = client.table("plenos").select("id, numero_acta, texto_completo").eq("estado", "procesado")
    if args.pleno:
        q = q.eq("numero_acta", args.pleno)
    plenos = q.execute().data

    print(f"Procesando {len(plenos)} plenos…\n")

    for pleno in plenos:
        pleno_id = pleno["id"]
        num = pleno["numero_acta"]
        texto_pleno = pleno.get("texto_completo") or ""

        # Puntos sin resumen
        puntos = (
            client.table("puntos")
            .select("id, numero, titulo, resultado, unanimidad")
            .eq("pleno_id", pleno_id)
            .is_("resumen_ia", "null")
            .order("numero")
            .execute()
            .data
        )

        if not puntos:
            print(f"  Acta {num}: todos los puntos ya tienen resumen.")
            continue

        print(f"  Acta {num}: {len(puntos)} puntos sin resumen…")

        for p in puntos:
            titulo   = p["titulo"]
            resultado = p["resultado"]
            # Extraer fragmento relevante del texto del pleno para este punto
            extracto = _extraer_fragmento(texto_pleno, p["numero"])
            resumen = generar_resumen_punto(titulo, resultado, extracto or titulo)
            if resumen:
                client.table("puntos").update({"resumen_ia": resumen[:600]}).eq("id", p["id"]).execute()
                print(f"    [{p['numero']}] OK — {resumen[:80]}…")
            else:
                print(f"    [{p['numero']}] Sin respuesta de Claude.")
            time.sleep(1)

    print("\nFin del backfill.")


def _extraer_fragmento(texto: str, numero: int) -> str:
    """Extrae hasta 3000 chars del cuerpo del punto N en el texto del pleno."""
    pat = re.compile(rf"\b{numero}\.-\s+[A-ZÁÉÍÓÚÑÜ]")
    m = pat.search(texto)
    if not m:
        return ""
    inicio = m.start()
    # Buscar el siguiente punto o fin
    siguiente = re.search(rf"\b{numero + 1}\.-\s+[A-ZÁÉÍÓÚÑÜ]", texto[inicio + 10:])
    fin = inicio + 10 + siguiente.start() if siguiente else inicio + 4000
    return texto[inicio:fin][:3000]


if __name__ == "__main__":
    main()
