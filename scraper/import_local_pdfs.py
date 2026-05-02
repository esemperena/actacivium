"""
Importa PDFs locales de actas en la BD.
Uso:
  python import_local_pdfs.py ../../actas_muestra/
  python import_local_pdfs.py ../../actas_muestra/ --reprocess
"""
import sys
import re
import time
import argparse
from pathlib import Path

from pdf_processor import (
    extraer_texto,
    extraer_metadatos,
    extraer_asistentes,
    extraer_puntos_sumario,
    extraer_votaciones_por_punto,
    clasificar_categoria,
    clasificar_tipo,
    clasificar_comision,
    generar_resumen_pleno,
)
import db
from run import _insertar_puntos

MUNICIPIO_NOMBRE = "San Sebastián"

# Nombre esperado: acta_NN_YYYYMMDD.pdf
FILENAME_PAT = re.compile(r"acta[_\-](\d+)[_\-](\d{4})(\d{2})(\d{2})\.pdf", re.IGNORECASE)


def _parsear_nombre(nombre: str) -> dict | None:
    m = FILENAME_PAT.match(nombre)
    if not m:
        return None
    num, año, mes, dia = m.groups()
    return {
        "numero_acta": int(num),
        "fecha_iso": f"{año}-{mes}-{dia}",
        "tipo": "extraordinaria" if "ex" in nombre.lower() else "ordinaria",
    }


def main():
    parser = argparse.ArgumentParser(description="Importar PDFs locales")
    parser.add_argument("directorio", type=Path, help="Carpeta con los PDFs")
    parser.add_argument("--reprocess", action="store_true", help="Borrar y reimportar si ya existe")
    args = parser.parse_args()

    municipio_id = db.get_municipio_id(MUNICIPIO_NOMBRE)
    pdfs = sorted(args.directorio.glob("acta_*.pdf"))

    if not pdfs:
        print("No se encontraron PDFs con patrón acta_*.pdf en", args.directorio)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Importación local — {len(pdfs)} PDFs encontrados")
    print(f"{'='*60}\n")

    ok = err = 0
    for pdf_path in pdfs:
        info = _parsear_nombre(pdf_path.name)
        if not info:
            print(f"  [!] Nombre no reconocido: {pdf_path.name} — saltado")
            continue

        num = info["numero_acta"]
        ya_existe = db.acta_ya_existe(municipio_id, num)

        if ya_existe and not args.reprocess:
            print(f"  [=] Acta {num} ya existe — usa --reprocess para reimportar")
            continue

        if ya_existe and args.reprocess:
            print(f"  [↺] Eliminando acta {num} para reimportar...")
            db.eliminar_pleno(municipio_id, num)

        print(f"  [{num}] {pdf_path.name}")
        exito = procesar_pdf_local(pdf_path, info, municipio_id)
        if exito:
            ok += 1
        else:
            err += 1
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"  OK: {ok} | Errores: {err}")
    print(f"{'='*60}\n")


def procesar_pdf_local(pdf_path: Path, info: dict, municipio_id: str) -> bool:
    pleno_id = db.insertar_pleno({
        "municipio_id": municipio_id,
        "numero_acta": info["numero_acta"],
        "fecha": info["fecha_iso"],
        "tipo_sesion": info["tipo"],
        "url_pdf_original": None,
        "estado": "pendiente",
    })
    print(f"    ↳ Pleno creado ({pleno_id[:8]}...)")

    try:
        print(f"    ↳ Extrayendo texto...", end=" ", flush=True)
        texto = extraer_texto(pdf_path)
        meta = extraer_metadatos(texto)
        asistentes, ausentes = extraer_asistentes(texto)
        puntos_sumario = extraer_puntos_sumario(texto)
        votaciones_por_punto = extraer_votaciones_por_punto(texto)
        n_con_votos = sum(1 for v in votaciones_por_punto.values() if v.get("partidos"))
        print(f"OK ({len(texto):,} chars, {len(puntos_sumario)} puntos, {n_con_votos} con votos)")

        print(f"    ↳ Generando resumen con Claude...", end=" ", flush=True)
        resumen_data = generar_resumen_pleno(texto)
        resumen_pleno = resumen_data.get("resumen_pleno", "") if resumen_data else ""
        puntos_ia = resumen_data.get("puntos", []) if resumen_data else []
        print(f"OK ({len(puntos_ia)} puntos clasificados)")

        db.actualizar_pleno(pleno_id, {
            "alcalde_nombre": meta.get("alcalde_nombre"),
            "secretaria_nombre": meta.get("secretaria_nombre"),
            "hora_inicio": meta.get("hora_inicio"),
            "texto_completo": texto,
            "resumen_ia": resumen_pleno,
            "n_puntos": len(puntos_ia) or len(puntos_sumario),
            "n_asistentes": len(asistentes),
            "n_ausentes": len(ausentes),
            "estado": "procesado",
            "procesado_at": "now()",
        })

        _insertar_puntos(pleno_id, municipio_id, puntos_ia, puntos_sumario, votaciones_por_punto)

        print(f"    ✓ Acta {info['numero_acta']} importada correctamente\n")
        return True

    except Exception as e:
        import traceback
        print(f"\n    [!] Error: {e}")
        traceback.print_exc()
        db.actualizar_pleno(pleno_id, {"estado": "error", "error_msg": str(e)[:500]})
        return False


if __name__ == "__main__":
    main()
