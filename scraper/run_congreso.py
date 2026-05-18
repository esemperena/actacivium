"""
Scraper de Acta Civium para el Congreso de los Diputados.

Uso:
  python run_congreso.py
  python run_congreso.py --dry-run
  python run_congreso.py --reprocess 150
  python run_congreso.py --limit 3
"""
import congreso
import pdf_processor_congreso
import db
from _run_core import main


def _descubrir(args, municipio_id):
    # Arranque incremental: comprobar HEAD solo desde el último DS conocido + 1
    # evita hacer cientos de HEAD requests en cada ejecución.
    if args.reprocess:
        desde_n = args.reprocess
    else:
        desde_n = db.max_numero_acta(municipio_id) + 1
    print(f"→ Buscando Diarios de Sesiones nuevos (desde nº {desde_n})...")
    return congreso.obtener_actas_disponibles(desde_n=desde_n)


if __name__ == "__main__":
    main(
        municipio_nombre="Congreso de los Diputados",
        descubrir_actas=_descubrir,
        scraper=congreso,
        processor=pdf_processor_congreso,
    )
