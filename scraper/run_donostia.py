"""
Scraper de Acta Civium para San Sebastián (Donostia).

Uso:
  python run_donostia.py
  python run_donostia.py --dry-run
  python run_donostia.py --reprocess 39
  python run_donostia.py --year 2024
  python run_donostia.py --limit 5
"""
import donostia
import pdf_processor
from _run_core import main


def _descubrir(args, municipio_id):
    print(f"→ Consultando actas disponibles en donostia.eus (año {args.year or 'actual'})...")
    return donostia.obtener_actas_disponibles(year=args.year)


if __name__ == "__main__":
    main(
        municipio_nombre="San Sebastián",
        descubrir_actas=_descubrir,
        scraper=donostia,
        processor=pdf_processor,
    )
