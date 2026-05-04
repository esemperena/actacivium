"""
Rellena la tabla asistencia para todos los plenos ya procesados,
leyendo el texto_completo que ya está en BD (sin re-descargar PDFs ni IA).

Uso:
  python backfill_asistencia.py
  python backfill_asistencia.py --dry-run   # muestra lo que haría sin insertar
"""
import argparse
import db
from pdf_processor import extraer_asistentes_con_partido

MUNICIPIO_NOMBRE = "San Sebastián"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    municipio_id = db.get_municipio_id(MUNICIPIO_NOMBRE)

    res = (
        db.get_client()
        .table("plenos")
        .select("id, numero_acta, texto_completo")
        .eq("municipio_id", municipio_id)
        .eq("estado", "procesado")
        .not_.is_("texto_completo", "null")
        .order("numero_acta")
        .execute()
    )
    plenos = res.data
    print(f"Plenos a procesar: {len(plenos)}\n")

    ok, sin_datos, errores = 0, 0, 0

    for p in plenos:
        num = p["numero_acta"]
        texto = p["texto_completo"] or ""
        registros = extraer_asistentes_con_partido(texto)

        presentes = sum(1 for r in registros if r["asistio"])
        ausentes  = sum(1 for r in registros if not r["asistio"])

        if not registros:
            print(f"  Acta {num:>3} — sin datos de asistencia")
            sin_datos += 1
            continue

        print(f"  Acta {num:>3} — {presentes} presentes, {ausentes} ausentes", end="")

        if args.dry_run:
            print("  [dry-run, no se inserta]")
            ok += 1
            continue

        # Limpiar asistencia previa (por si se ejecuta más de una vez)
        db.limpiar_asistencia_pleno(p["id"])

        filas = []
        for r in registros:
            partido_id = None
            if r.get("partido_raw"):
                partido_id = db.get_partido_id(municipio_id, r["partido_raw"])
            filas.append({
                "pleno_id": p["id"],
                "nombre_raw": r["nombre"],
                "partido_id": partido_id,
                "asistio": r["asistio"],
            })

        con_partido = sum(1 for f in filas if f["partido_id"])
        db.insertar_asistencia_bulk(filas)
        print(f"  ({con_partido}/{len(filas)} con partido resuelto)")
        ok += 1

    print(f"\n✓ {ok} procesadas · {sin_datos} sin datos · {errores} errores")


if __name__ == "__main__":
    main()
