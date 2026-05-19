"""Reprocesa TODAS las actas de la BD con el extractor mejorado de votaciones.

Uso:
  python reprocess_all.py           # reprocesa todo
  python reprocess_all.py --year 2024  # solo un año
  python reprocess_all.py --from-acta 40  # desde un número de acta

El año se deduce automáticamente de la fecha de cada pleno.
"""
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import db


def main():
    parser = argparse.ArgumentParser(description="Reprocesado completo de actas")
    parser.add_argument("--year", type=int, help="Filtrar solo un año concreto")
    parser.add_argument("--from-acta", type=int, metavar="N", help="Empezar desde acta nº N")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar, no ejecutar")
    args = parser.parse_args()

    municipio_id = db.get_municipio_id("San Sebastián")
    client = db.get_client()

    query = (
        client.table("plenos")
        .select("numero_acta, fecha, tipo_sesion, url_pdf_original")
        .eq("institucion_id", municipio_id)
        .order("numero_acta")
    )
    if args.year:
        query = query.gte("fecha", f"{args.year}-01-01").lt("fecha", f"{args.year + 1}-01-01")
    if args.from_acta:
        query = query.gte("numero_acta", args.from_acta)

    plenos = query.execute().data
    print(f"\nTotal actas a reprocesar: {len(plenos)}\n")

    sin_url = [p for p in plenos if not p.get("url_pdf_original")]
    if sin_url:
        print(f"⚠  Actas SIN URL almacenada ({len(sin_url)}) — se buscará en donostia.eus por año:")
        for p in sin_url:
            year = datetime.fromisoformat(p["fecha"]).year
            print(f"     Acta {p['numero_acta']:>3} | {p['fecha']} | año={year}")
        print()

    if args.dry_run:
        print("(dry-run: no se ejecuta nada)")
        return

    ok, errores = 0, 0
    for i, p in enumerate(plenos, 1):
        num = p["numero_acta"]
        year = datetime.fromisoformat(p["fecha"]).year
        tipo = p.get("tipo_sesion", "")
        tiene_url = bool(p.get("url_pdf_original"))

        print(f"\n{'='*60}")
        print(f"[{i}/{len(plenos)}] Acta {num} ({p['fecha']}, {tipo}){'' if tiene_url else ' ⚠ sin URL'}")
        print(f"{'='*60}")

        result = subprocess.run(
            [sys.executable, "-X", "utf8", "run.py",
             "--year", str(year),
             "--reprocess", str(num)],
            cwd=Path(__file__).parent,
            capture_output=False,
        )
        if result.returncode != 0:
            print(f"  ✗ ERROR: acta {num} falló (código {result.returncode})")
            errores += 1
        else:
            ok += 1

    print(f"\n{'='*60}")
    print(f"  Completado | OK: {ok} | Errores: {errores}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
