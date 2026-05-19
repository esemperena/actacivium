"""
Pipeline central de Acta Civium.
No se ejecuta directamente — cada institución tiene su propio entry point:
  run_donostia.py, run_congreso.py, etc.

Uso desde entry point:
  from _run_core import main
  main(
      municipio_nombre="San Sebastián",
      descubrir_actas=lambda args, mid: scraper.obtener_actas_disponibles(year=args.year),
      scraper=donostia,
      processor=pdf_processor,
  )
"""
import time
import argparse
from pathlib import Path
from datetime import datetime
from types import ModuleType

from config import PDF_TEMP_DIR
import db

TIPOS_CON_PROPONENTE = {
    "mocion",
    "proposicion_normativa",
    "interpelacion",
    "pregunta_oral",
    "pregunta_escrita",
    "ruego",
    "declaracion_institucional",
}


def main(
    municipio_nombre: str,
    descubrir_actas,       # callable(args, municipio_id) → list[ActaRef]
    scraper: ModuleType,   # módulo con descargar_pdf, fecha_str_a_iso
    processor: ModuleType, # módulo con extraer_texto, clasificar_*, generar_*, etc.
):
    parser = argparse.ArgumentParser(description=f"Acta Civium — {municipio_nombre}")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar, no procesar")
    parser.add_argument("--reprocess", type=int, metavar="N", help="Reprocesar acta nº N")
    parser.add_argument("--year", type=int, metavar="YYYY", help="Año (solo municipios con URL por año)")
    parser.add_argument("--limit", type=int, metavar="N", help="Procesar como máximo N actas nuevas")
    parser.add_argument("--no-newsletter", action="store_true", help="No enviar newsletter")
    args = parser.parse_args()

    inicio = time.time()
    municipio_id = db.get_municipio_id(municipio_nombre)
    temp_dir = Path(PDF_TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Acta Civium — Scraper | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Institución: {municipio_nombre}")
    print(f"{'='*60}\n")

    # 1. Descubrir actas disponibles (estrategia delegada al entry point)
    actas = descubrir_actas(args, municipio_id)
    print(f"  {len(actas)} actas encontradas\n")

    if args.dry_run:
        _mostrar_actas_nuevas(actas, municipio_id)
        return

    # 2. Filtrar las que no están en BD (o la pedida con --reprocess)
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

    if args.limit:
        actas_a_procesar = actas_a_procesar[:args.limit]

    print(f"→ {len(actas_a_procesar)} actas nuevas a procesar:\n")

    # 3. Procesar cada acta
    procesadas, errores = 0, 0
    for acta in actas_a_procesar:
        print(f"  [{acta.numero_acta}] {acta.fecha_str or '(fecha pendiente)'} ({acta.tipo})")
        if args.reprocess:
            db.eliminar_pleno(municipio_id, acta.numero_acta)
        pleno_id = _procesar_acta(acta, municipio_id, temp_dir, scraper, processor)
        if pleno_id:
            procesadas += 1
            if not args.no_newsletter and not args.reprocess:
                try:
                    from send_newsletter import enviar_newsletter
                    enviar_newsletter(pleno_id, municipio_nombre=municipio_nombre)
                except Exception as e:
                    print(f"    [!] Error enviando newsletter: {e}")
        else:
            errores += 1
        time.sleep(2)

    duracion = time.time() - inicio
    print(f"\n{'='*60}")
    print(f"  Completado en {duracion:.1f}s | Nuevas: {procesadas} | Errores: {errores}")
    print(f"{'='*60}\n")

    _registrar_log(municipio_id, procesadas, errores, inicio)


def _procesar_acta(acta, municipio_id: str, temp_dir: Path,
                   scraper: ModuleType, processor: ModuleType) -> str | None:
    """Descarga, parsea, analiza y persiste una acta. Devuelve pleno_id o None."""

    fecha_iso = scraper.fecha_str_a_iso(acta.fecha_str)
    # Si la fecha es desconocida (p.ej. Congreso antes de descargar el PDF),
    # usamos hoy como placeholder y la corregimos tras extraer el texto.
    fecha_para_insert = fecha_iso or datetime.now().strftime("%Y-%m-%d")

    pleno_id = db.insertar_pleno({
        "institucion_id": municipio_id,
        "numero_acta": acta.numero_acta,
        "fecha": fecha_para_insert,
        "tipo_sesion": acta.tipo,
        "url_pdf_original": acta.url_pdf,
        "estado": "pendiente",
    })
    print(f"    ↳ Pleno creado (id: {pleno_id[:8]}...)")

    try:
        # Descarga
        pdf_path = temp_dir / acta.nombre_pdf
        print(f"    ↳ Descargando PDF...", end=" ", flush=True)
        if not scraper.descargar_pdf(acta.url_pdf, pdf_path):
            raise RuntimeError("Fallo en descarga del PDF")
        print(f"OK ({pdf_path.stat().st_size // 1024} KB)")

        # Extracción de texto y parsing estructurado
        print(f"    ↳ Extrayendo texto...", end=" ", flush=True)
        texto = processor.extraer_texto(pdf_path)
        texto_cas = processor.extraer_texto_castellano(pdf_path)
        meta = processor.extraer_metadatos(texto)
        asistentes, ausentes = processor.extraer_asistentes(texto)
        puntos_sumario = processor.extraer_puntos_sumario(texto)
        votaciones_por_punto = processor.extraer_votaciones_por_punto(texto_cas)
        n_con_votos = sum(1 for v in votaciones_por_punto.values() if v.get("partidos"))
        print(f"OK ({len(texto):,} chars, {len(puntos_sumario)} puntos, {n_con_votos} con votos)")

        # Corregir fecha si era placeholder
        if not fecha_iso and meta.get("fecha_iso"):
            db.actualizar_pleno(pleno_id, {"fecha": meta["fecha_iso"]})

        # Resumen del pleno
        print(f"    ↳ Generando resumen del pleno...", end=" ", flush=True)
        resumen_pleno = processor.generar_resumen_pleno(texto) or ""
        print(f"OK ({len(resumen_pleno)} chars)")

        # Actualizar pleno con datos completos
        db.actualizar_pleno(pleno_id, {
            "alcalde_nombre": meta.get("alcalde_nombre") or meta.get("presidenta_nombre"),
            "secretaria_nombre": meta.get("secretaria_nombre"),
            "hora_inicio": meta.get("hora_inicio"),
            "texto_completo": texto,
            "resumen_ia": resumen_pleno,
            "n_puntos": len(puntos_sumario),
            "n_asistentes": len(asistentes),
            "n_ausentes": len(ausentes),
            "estado": "procesado",
            "procesado_at": "now()",
        })

        # Asistencia
        asistencia_detalle = processor.extraer_asistentes_con_partido(texto)
        if asistencia_detalle:
            _insertar_asistencia(pleno_id, municipio_id, asistencia_detalle)
            presentes = sum(1 for r in asistencia_detalle if r["asistio"])
            ausentes_n = sum(1 for r in asistencia_detalle if not r["asistio"])
            print(f"    ↳ Asistencia: {presentes} presentes, {ausentes_n} ausentes")

        # Puntos y votaciones
        print(f"    ↳ Generando resúmenes de {len(puntos_sumario)} puntos...", flush=True)
        _insertar_puntos(pleno_id, municipio_id, puntos_sumario, votaciones_por_punto, texto, processor)

        pdf_path.unlink(missing_ok=True)
        print(f"    ✓ Acta {acta.numero_acta} procesada correctamente\n")
        return pleno_id

    except Exception as e:
        print(f"\n    [!] Error procesando acta {acta.numero_acta}: {e}")
        db.actualizar_pleno(pleno_id, {"estado": "error", "error_msg": str(e)[:500]})
        return None


def _insertar_puntos(pleno_id: str, municipio_id: str, puntos_sumario: list,
                     votaciones_por_punto: dict, texto_completo: str,
                     processor: ModuleType):
    for p in puntos_sumario:
        num = p["numero"]
        titulo = p["titulo"]
        vot = votaciones_por_punto.get(num, {})
        resultado = vot.get("resultado") or "sin_votacion"
        unanimidad = vot.get("unanimidad")

        categoria = processor.clasificar_categoria(titulo)
        tipo = processor.clasificar_tipo(titulo)
        comision = processor.clasificar_comision(titulo)

        extracto = processor._extraer_fragmento(texto_completo, num) if texto_completo else titulo
        texto_para_resumen = extracto or titulo
        resumen_ia = processor.generar_resumen_punto(titulo, resultado, texto_para_resumen)

        if processor._titulo_necesita_reescritura(titulo):
            titulo_reescrito = processor.generar_titulo_punto(titulo, resultado, texto_para_resumen)
            if titulo_reescrito:
                titulo = titulo_reescrito

        grupo_proponente_raw = (
            processor.extraer_grupo_proponente_raw(titulo, extracto)
            if tipo in TIPOS_CON_PROPONENTE else None
        )
        grupo_proponente_id = (
            db.get_partido_id(municipio_id, grupo_proponente_raw)
            if grupo_proponente_raw else None
        )
        relevancia_social = processor.calcular_relevancia_social(
            titulo,
            categoria=categoria,
            tipo=tipo,
            resultado=resultado,
            unanimidad=unanimidad,
            resumen=resumen_ia or "",
            texto=extracto,
        )
        print(f"      [{num}] {titulo[:60]!r} → {resumen_ia[:70] if resumen_ia else 'sin resumen'}…")

        punto_id = db.insertar_punto({
            "pleno_id": pleno_id,
            "numero": num,
            "titulo": titulo,
            "comision": comision,
            "tipo": tipo,
            "categoria": categoria,
            "resultado": resultado,
            "unanimidad": unanimidad,
            "grupo_proponente_id": grupo_proponente_id,
            "texto_completo": extracto or None,
            "resumen_ia": resumen_ia[:600] if resumen_ia else None,
            "relevancia_social": relevancia_social,
            "es_urgencia": p.get("es_urgencia", False),
        })

        for siglas, votos in vot.get("partidos", {}).items():
            partido_id = db.get_partido_id(municipio_id, siglas)
            if not partido_id:
                continue
            try:
                db.insertar_votacion({
                    "punto_id": punto_id,
                    "partido_id": partido_id,
                    "votos_favor": votos.get("votos_favor", 0),
                    "votos_contra": votos.get("votos_contra", 0),
                    "abstenciones": votos.get("abstenciones", 0),
                    "ausentes": votos.get("ausentes", 0),
                })
            except Exception:
                pass


def _mostrar_actas_nuevas(actas, municipio_id: str):
    print("Modo dry-run — actas nuevas (no en BD):\n")
    nuevas = [a for a in actas if not db.acta_ya_existe(municipio_id, a.numero_acta)]
    if not nuevas:
        print("  Ninguna. Todo al día.")
        return
    for a in nuevas:
        print(f"  Acta {a.numero_acta:>3} | {a.fecha_str or '?'} | {a.tipo:<14} | {a.url_pdf}")


def _insertar_asistencia(pleno_id: str, municipio_id: str, registros: list[dict]):
    filas = []
    for r in registros:
        partido_id = db.get_partido_id(municipio_id, r["partido_raw"]) if r.get("partido_raw") else None
        filas.append({
            "pleno_id": pleno_id,
            "nombre_raw": r["nombre"],
            "partido_id": partido_id,
            "asistio": r["asistio"],
        })
    db.insertar_asistencia_bulk(filas)


def _registrar_log(municipio_id: str, nuevas: int, errores: int, inicio: float):
    db.registrar_log(municipio_id, nuevas, errores, time.time() - inicio, {})
