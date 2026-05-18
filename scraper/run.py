"""
Alias de compatibilidad → apunta a run_donostia.py.
Mantiene el Task Scheduler existente funcionando sin cambios.

Para el Congreso usar: python run_congreso.py
"""
from run_donostia import _descubrir
import donostia, pdf_processor
from _run_core import main

if __name__ == "__main__":
    main(
        municipio_nombre="San Sebastián",
        descubrir_actas=_descubrir,
        scraper=donostia,
        processor=pdf_processor,
    )
