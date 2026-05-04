"""
Rellena grupo_proponente_id y relevancia_social para puntos ya existentes.

Uso:
  py backfill_puntos_metadata.py
  py backfill_puntos_metadata.py --pleno 45
  py backfill_puntos_metadata.py --overwrite
  py backfill_puntos_metadata.py --dry-run
"""
import argparse

import db
from backfill_resumenes import _extraer_fragmento
from pdf_processor import extraer_grupo_proponente_raw, calcular_relevancia_social

MUNICIPIO_NOMBRE = "San Sebastián"
TIPOS_CON_PROPONENTE = {
    "mocion",
    "proposicion_normativa",
    "interpelacion",
    "pregunta_oral",
    "pregunta_escrita",
    "ruego",
    "declaracion_institucional",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pleno", type=int, help="Número de acta a procesar")
    parser.add_argument("--overwrite", action="store_true",
                        help="Recalcular aunque el punto ya tenga datos")
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra los cambios sin escribir en la BD")
    args = parser.parse_args()

    client = db.get_client()
    municipio_id = db.get_municipio_id(MUNICIPIO_NOMBRE)

    q = (
        client.table("plenos")
        .select("id, numero_acta, texto_completo")
        .eq("municipio_id", municipio_id)
        .eq("estado", "procesado")
        .order("numero_acta")
    )
    if args.pleno:
        q = q.eq("numero_acta", args.pleno)

    plenos = q.execute().data or []
    print(f"Plenos a procesar: {len(plenos)}\n")

    updated = 0
    skipped = 0

    for pleno in plenos:
        pleno_id = pleno["id"]
        numero_acta = pleno["numero_acta"]
        texto_pleno = pleno.get("texto_completo") or ""

        puntos = (
            client.table("puntos")
            .select("id, numero, titulo, categoria, tipo, resultado, unanimidad, resumen_ia, grupo_proponente_id, relevancia_social")
            .eq("pleno_id", pleno_id)
            .order("numero")
            .execute()
            .data
            or []
        )

        print(f"Acta {numero_acta}: {len(puntos)} puntos")
        for punto in puntos:
            needs_proponente = args.overwrite or not punto.get("grupo_proponente_id")
            needs_relevancia = args.overwrite or punto.get("relevancia_social") is None
            if not needs_proponente and not needs_relevancia:
                skipped += 1
                continue

            extracto = _extraer_fragmento(texto_pleno, punto["numero"]) if texto_pleno else ""
            grupo_raw = (
                extraer_grupo_proponente_raw(punto.get("titulo") or "", extracto)
                if punto.get("tipo") in TIPOS_CON_PROPONENTE else None
            )
            grupo_id = db.get_partido_id(municipio_id, grupo_raw) if grupo_raw else None
            relevancia = calcular_relevancia_social(
                punto.get("titulo") or "",
                categoria=punto.get("categoria"),
                tipo=punto.get("tipo"),
                resultado=punto.get("resultado"),
                unanimidad=punto.get("unanimidad"),
                resumen=punto.get("resumen_ia") or "",
                texto=extracto,
            )

            payload = {}
            if needs_proponente:
                payload["grupo_proponente_id"] = grupo_id
            if needs_relevancia:
                payload["relevancia_social"] = relevancia

            if not payload:
                skipped += 1
                continue

            if args.dry_run:
                print(
                    f"  [{punto['numero']}] {punto['titulo'][:70]!r} "
                    f"→ proponente={grupo_raw or '-'} relevancia={relevancia}"
                )
            else:
                db.actualizar_punto(punto["id"], payload)
                print(
                    f"  [{punto['numero']}] actualizado "
                    f"(proponente={grupo_raw or '-'} relevancia={relevancia})"
                )
            updated += 1

        print()

    print(f"Fin. Actualizados: {updated} · Omitidos: {skipped}")


if __name__ == "__main__":
    main()
