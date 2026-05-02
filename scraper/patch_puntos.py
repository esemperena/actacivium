"""
Patch script: inserts puntos for plenos that already exist in Supabase
but have 0 puntos (e.g. after fixing the sumario extractor).

Usage:
  cd actacivium/scraper
  python patch_puntos.py
"""
import sys
from pathlib import Path

# Reuse helpers and logic from import_actas
sys.path.insert(0, str(Path(__file__).parent))
from import_actas import (
    ACTAS_DIR, HEADERS, SUPABASE_URL,
    sb_get, sb_post,
    extraer_texto, extraer_meta, extraer_sumario,
    clasificar, relevancia, CATS, TIPOS,
)

import httpx


def delete_puntos(pleno_id: str) -> None:
    r = httpx.delete(
        f"{SUPABASE_URL}/rest/v1/puntos",
        headers=HEADERS,
        params={"pleno_id": f"eq.{pleno_id}"},
        timeout=15,
    )
    r.raise_for_status()


def patch_acta(pdf_path: Path) -> None:
    nombre = pdf_path.name
    print(f"\n  {nombre}")

    texto   = extraer_texto(pdf_path)
    meta    = extraer_meta(texto, nombre)
    sumario = extraer_sumario(texto)

    if not meta.get("numero_acta"):
        print("    ✗ No se pudo extraer número de acta, saltando.")
        return

    # Find existing pleno
    plenos = sb_get("plenos", {
        "numero_acta": f"eq.{meta['numero_acta']}",
        "select": "id,n_puntos",
    })
    if not plenos:
        print(f"    ✗ Pleno {meta['numero_acta']} no encontrado en Supabase.")
        return

    pleno = plenos[0]
    pleno_id = pleno["id"]
    print(f"    pleno_id: {pleno_id[:8]}…  puntos actuales: {pleno['n_puntos']}  →  {len(sumario)} extraídos")

    # Delete existing puntos and re-insert
    delete_puntos(pleno_id)

    for p in sumario:
        cat  = clasificar(p["titulo"], CATS)
        tipo = clasificar(p["titulo"], TIPOS)
        try:
            sb_post("puntos", {
                "pleno_id":          pleno_id,
                "numero":            p["numero"],
                "titulo":            p["titulo"][:500],
                "categoria":         cat,
                "tipo":              tipo,
                "comision":          "pleno",
                "resultado":         "sin_votacion",
                "unanimidad":        None,
                "resumen_ia":        None,
                "relevancia_social": relevancia(p["titulo"], cat),
                "es_urgencia":       False,
            })
        except Exception as e:
            print(f"    ✗ Error en punto {p['numero']}: {e}")

    # Update n_puntos on pleno
    r = httpx.patch(
        f"{SUPABASE_URL}/rest/v1/plenos",
        headers=HEADERS,
        params={"id": f"eq.{pleno_id}"},
        json={"n_puntos": len(sumario)},
        timeout=15,
    )
    r.raise_for_status()
    print(f"    ✓ {len(sumario)} puntos insertados")


def main() -> None:
    print("\n" + "═" * 55)
    print("  Acta Civium — Patch de puntos")
    print("═" * 55)

    pdfs = sorted(ACTAS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"❌  No hay PDFs en {ACTAS_DIR}")
        sys.exit(1)

    for pdf in pdfs:
        patch_acta(pdf)

    print(f"\n{'═'*55}\n  Completado\n{'═'*55}\n")


if __name__ == "__main__":
    main()
