"""
Punto de entrada del scraper de Acta Civium.
Ejecutar manualmente o via Windows Task Scheduler.

Uso:
  python run.py                     # procesa San Sebastián
  python run.py --dry-run           # muestra actas nuevas sin procesar
  python run.py --reprocess 39      # reprocesa el acta nº 39
"""
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

from config import PDF_TEMP_DIR
from donostia import (
    obtener_actas_disponibles,
    descargar_pdf,
    fecha_str_a_iso,
)
from pdf_processor import (
    extraer_texto,
    extraer_metadatos,
    extraer_asistentes,
    extraer_puntos_sumario,
    extraer_votaciones_texto,
    clasificar_categoria,
    clasificar_tipo,
    clasificar_comision,
    generar_resumen_pleno,
)
import db

MUNICIPIO_NOMBRE = "San Sebastián"


def main():
    parser = argparse.ArgumentParser(description="Scraper Acta Civium")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar, no procesar")
    parser.add_argument("--reprocess", type=int, metavar="N", help="Reprocesar acta nº N")
    args = parser.parse_args()

    inicio = time.time()
    municipio_id = db.get_municipio_id(MUNICIPIO_NOMBRE)
    temp_dir = Path(PDF_TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Acta Civium — Scraper | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Municipio: {MUNICIPIO_NOMBRE}")
    print(f"{'='*60}\n")

    # 1. Obtener lista de actas disponibles en la web
    print("→ Consultando actas disponibles en donostia.eus...")
    actas = obtener_actas_disponibles()
    print(f"  {len(actas)} actas encontradas en la web\n")

    if args.dry_run:
        _mostrar_actas_nuevas(actas, municipio_id)
        return

    # 2. Filtrar solo las que no están en la BD (o la solicitada para reprocesar)
    actas_a_procesar = []
    for acta in actas:
        if args.reprocess:
            if acta.numero_acta == args.reprocess:
                actas_a_procesar.append(acta)
        else:
            if not db.acta_ya_existe(municipio_id, acta.numero_acta):
                actas_a_procesar.append(acta)

    if not actas_a_procesar:
        print("✓ No hay actas nuevas. Todo al día.\n")
        _registrar_log(municipio_id, 0, 0, inicio)
        return

    print(f"→ {len(actas_a_procesar)} actas nuevas a procesar:\n")

    # 3. Procesar cada acta nueva
    procesadas, errores = 0, 0
    for acta in actas_a_procesar:
        print(f"  [{acta.numero_acta}] {acta.fecha_str} ({acta.tipo})")
        exito = procesar_acta(acta, municipio_id, temp_dir)
        if exito:
            procesadas += 1
        else:
            errores += 1
        time.sleep(2)  # pausa educada entre peticiones

    duracion = time.time() - inicio
    print(f"\n{'='*60}")
    print(f"  Completado en {duracion:.1f}s | Nuevas: {procesadas} | Errores: {errores}")
    print(f"{'='*60}\n")

    _registrar_log(municipio_id, procesadas, errores, inicio)


def procesar_acta(acta, municipio_id: str, temp_dir: Path) -> bool:
    """Descarga, extrae, analiza con IA e inserta en BD una acta completa."""

    # ── Insertar pleno en estado 'pendiente' ──────────────────────────────────
    fecha_iso = fecha_str_a_iso(acta.fecha_str)
    pleno_id = db.insertar_pleno({
        "municipio_id": municipio_id,
        "numero_acta": acta.numero_acta,
        "fecha": fecha_iso,
        "tipo_sesion": acta.tipo,
        "url_pdf_original": acta.url_pdf,
        "estado": "pendiente",
    })
    print(f"    ↳ Pleno creado (id: {pleno_id[:8]}...)")

    try:
        # ── Descargar PDF ─────────────────────────────────────────────────────
        pdf_path = temp_dir / acta.nombre_pdf
        print(f"    ↳ Descargando PDF...", end=" ", flush=True)
        if not descargar_pdf(acta.url_pdf, pdf_path):
            raise RuntimeError("Fallo en descarga del PDF")
        print(f"OK ({pdf_path.stat().st_size // 1024} KB)")

        # ── Extraer texto ─────────────────────────────────────────────────────
        print(f"    ↳ Extrayendo texto...", end=" ", flush=True)
        texto = extraer_texto(pdf_path)
        meta = extraer_metadatos(texto)
        asistentes, ausentes = extraer_asistentes(texto)
        puntos_sumario = extraer_puntos_sumario(texto)
        print(f"OK ({len(texto):,} chars, {len(puntos_sumario)} puntos en sumario)")

        # ── Generar resumen con Claude CLI ────────────────────────────────────
        print(f"    ↳ Generando resumen con Claude...", end=" ", flush=True)
        resumen_data = generar_resumen_pleno(texto)
        resumen_pleno = resumen_data.get("resumen_pleno", "") if resumen_data else ""
        puntos_ia = resumen_data.get("puntos", []) if resumen_data else []
        print(f"OK ({len(puntos_ia)} puntos clasificados)")

        # ── Actualizar pleno con datos completos ──────────────────────────────
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

        # ── Insertar puntos del orden del día ─────────────────────────────────
        _insertar_puntos(pleno_id, municipio_id, puntos_ia, puntos_sumario)

        # ── Limpiar PDF temporal ──────────────────────────────────────────────
        pdf_path.unlink(missing_ok=True)

        print(f"    ✓ Acta {acta.numero_acta} procesada correctamente\n")
        return True

    except Exception as e:
        print(f"\n    [!] Error procesando acta {acta.numero_acta}: {e}")
        db.actualizar_pleno(pleno_id, {"estado": "error", "error_msg": str(e)[:500]})
        return False


def _insertar_puntos(pleno_id: str, municipio_id: str, puntos_ia: list, puntos_sumario: list):
    """Inserta los puntos del orden del día en la BD."""
    # Preferimos los datos enriquecidos de la IA; sumario como fallback
    fuente = puntos_ia if puntos_ia else [
        {"numero": p["numero"], "titulo": p["titulo"],
         "categoria": clasificar_categoria(p["titulo"]),
         "tipo": clasificar_tipo(p["titulo"]),
         "comision": clasificar_comision(p["titulo"]),
         "resultado": "sin_votacion", "unanimidad": None,
         "relevancia_social": None, "resumen_ia": None}
        for p in puntos_sumario
    ]

    for p in fuente:
        db.insertar_punto({
            "pleno_id": pleno_id,
            "numero": p.get("numero", 0),
            "titulo": p.get("titulo", ""),
            "comision": p.get("comision", "otro"),
            "tipo": p.get("tipo", "otro"),
            "categoria": p.get("categoria", "otro"),
            "resultado": p.get("resultado", "sin_votacion"),
            "unanimidad": p.get("unanimidad"),
            "resumen_ia": p.get("resumen_ia"),
            "relevancia_social": p.get("relevancia_social"),
            "es_urgencia": p.get("es_urgencia", False),
        })


def _mostrar_actas_nuevas(actas, municipio_id: str):
    print("Modo dry-run — actas nuevas (no en BD):\n")
    nuevas = [a for a in actas if not db.acta_ya_existe(municipio_id, a.numero_acta)]
    if not nuevas:
        print("  Ninguna. Todo al día.")
        return
    for a in nuevas:
        print(f"  Acta {a.numero_acta:>3} | {a.fecha_str} | {a.tipo:<14} | {a.url_pdf}")


def _registrar_log(municipio_id: str, nuevas: int, errores: int, inicio: float):
    db.registrar_log(municipio_id, nuevas, errores, time.time() - inicio, {})


if __name__ == "__main__":
    main()
