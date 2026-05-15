#!/usr/bin/env python3
"""
Correcciones para los datos de Donostia:
  1. Genera resumen_ia de pleno para actas sin él (#44, #39, #36, #35)
  2. Genera resumen_ia para puntos sin él en esas actas
  3. Limpia títulos con código duplicado en el acta #35

Uso:
  python fix_donostia.py               # todo
  python fix_donostia.py --only-resumenes
  python fix_donostia.py --only-puntos
  python fix_donostia.py --only-titles
"""

import argparse
import re
import sys
import time

sys.path.insert(0, ".")
from db import get_client
from pdf_processor import generar_resumen_pleno, generar_resumen_punto


def _extraer_fragmento(texto: str, numero: int) -> str:
    """Extrae hasta 3000 chars del cuerpo del punto N en el texto del pleno."""
    pat = re.compile(rf"\b{numero}\.-\s+[A-ZÁÉÍÓÚÑÜ]")
    m = pat.search(texto)
    if not m:
        return ""
    inicio = m.start()
    siguiente = re.search(rf"\b{numero + 1}\.-\s+[A-ZÁÉÍÓÚÑÜ]", texto[inicio + 10:])
    fin = inicio + 10 + siguiente.start() if siguiente else inicio + 4000
    return texto[inicio:fin][:3000]

# ── Actas que necesitan correcciones ─────────────────────────────────────────
ACTAS_SIN_RESUMEN = [44, 39, 36, 35]

# Puntos del acta #35 con códigos duplicados al final del título
# Patrón: "(CÓDIGO) ... (CÓDIGO)" → limpiar el código final si ya aparece antes
_RE_CODIGO_DUPLICADO = re.compile(
    r"(\([A-Z0-9\-]+\))(\s+\S.+?)\s+\1\s*$"
)
# También: título que termina con "(código)" duplicado sin otro texto entre medias
_RE_CODIGO_SUFIJO = re.compile(r"\s+(\([A-Z0-9\-]{3,}\))\s*$")


def limpiar_titulo_duplicado(titulo: str) -> str:
    """Elimina sufijos con código de referencia duplicado al final del título."""
    # Caso: "texto (CODE) más texto (CODE)" → quitar el segundo (CODE)
    m = _RE_CODIGO_DUPLICADO.search(titulo)
    if m:
        # Reconstruir sin el segundo código
        limpio = titulo[:m.start()] + m.group(1) + m.group(2)
        return limpio.strip(" .,")

    # Caso: "texto (OTA). (ORER-11)" → "(ORER-11)" es redundante si OTA ya está
    # Detectar patrones como "...(OTA). (ORER-XX)"
    m2 = re.search(r"\.\s+\([A-Z0-9\-]+\)\s*$", titulo)
    if m2:
        # Comprobar que el código antes del punto ya dice algo
        antes = titulo[:m2.start()]
        if len(antes) > 30:
            return antes.strip(" .,")

    return titulo


def paso1_resumenes_plenos(client, plenos_sin_resumen: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("PASO 1: Generando resumen_ia para plenos sin resumen")
    print("=" * 70)

    for pleno in plenos_sin_resumen:
        num = pleno["numero_acta"]
        texto = pleno.get("texto_completo") or ""
        if not texto:
            print(f"  Acta #{num}: sin texto completo, no se puede generar resumen.")
            continue

        print(f"  Acta #{num} ({pleno['fecha']}): generando... ", end="", flush=True)
        resumen = generar_resumen_pleno(texto)
        if resumen:
            client.table("plenos").update({"resumen_ia": resumen}).eq("id", pleno["id"]).execute()
            print(f"OK ({len(resumen)} chars)")
            print(f"    {resumen[:120]}...")
        else:
            print("Sin respuesta de Claude.")
        time.sleep(2)


def paso2_resumenes_puntos(client, plenos: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("PASO 2: Generando resumen_ia para puntos sin resumen")
    print("=" * 70)

    for pleno in plenos:
        num = pleno["numero_acta"]
        texto_pleno = pleno.get("texto_completo") or ""

        puntos = (
            client.table("puntos")
            .select("id, numero, titulo, resultado, resumen_ia")
            .eq("pleno_id", pleno["id"])
            .order("numero")
            .execute()
            .data
        )

        pendientes = [p for p in puntos if not p.get("resumen_ia")]
        if not pendientes:
            print(f"  Acta #{num}: todos los puntos ya tienen resumen.")
            continue

        print(f"  Acta #{num}: {len(pendientes)} puntos sin resumen...")

        for p in pendientes:
            titulo = p.get("titulo") or ""
            resultado = p.get("resultado") or "sin_votacion"
            extracto = _extraer_fragmento(texto_pleno, p["numero"])
            texto_para_resumen = extracto if extracto else titulo

            print(f"    [{p['numero']}] {titulo[:55]}... ", end="", flush=True)
            resumen = generar_resumen_punto(titulo, resultado, texto_para_resumen)
            if resumen:
                client.table("puntos").update({"resumen_ia": resumen[:600]}).eq("id", p["id"]).execute()
                print(f"OK")
            else:
                print("Sin respuesta.")
            time.sleep(1)


def paso3_limpiar_titulos(client, pleno_35: dict) -> None:
    print("\n" + "=" * 70)
    print("PASO 3: Limpiando títulos con código duplicado (Acta #35)")
    print("=" * 70)

    puntos = (
        client.table("puntos")
        .select("id, numero, titulo")
        .eq("pleno_id", pleno_35["id"])
        .order("numero")
        .execute()
        .data
    )

    corregidos = 0
    for p in puntos:
        titulo_original = p.get("titulo") or ""
        if len(titulo_original) <= 200:
            continue

        titulo_limpio = limpiar_titulo_duplicado(titulo_original)
        if titulo_limpio != titulo_original:
            print(f"  Punto {p['numero']}:")
            print(f"    ANTES: {titulo_original[-80:]}")
            print(f"    DESPUES: {titulo_limpio[-80:]}")
            client.table("puntos").update({"titulo": titulo_limpio}).eq("id", p["id"]).execute()
            corregidos += 1

    if corregidos:
        print(f"\n  {corregidos} títulos corregidos.")
    else:
        print("  No se encontraron títulos con código duplicado.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-resumenes", action="store_true")
    parser.add_argument("--only-puntos", action="store_true")
    parser.add_argument("--only-titles", action="store_true")
    args = parser.parse_args()

    do_all = not any([args.only_resumenes, args.only_puntos, args.only_titles])

    client = get_client()

    # Obtener municipio
    muni = client.table("municipios").select("id").eq("slug", "san-sebastian").execute()
    municipio_id = muni.data[0]["id"]

    # Obtener plenos sin resumen
    plenos_sin_resumen = (
        client.table("plenos")
        .select("id, numero_acta, fecha, texto_completo, resumen_ia")
        .eq("municipio_id", municipio_id)
        .eq("estado", "procesado")
        .is_("resumen_ia", "null")
        .order("numero_acta")
        .execute()
        .data
    )

    # También los que tienen texto pero resumen vacío (string vacío)
    todos_plenos = (
        client.table("plenos")
        .select("id, numero_acta, fecha, texto_completo, resumen_ia")
        .eq("municipio_id", municipio_id)
        .eq("estado", "procesado")
        .order("numero_acta")
        .execute()
        .data
    )
    plenos_sin_resumen = [p for p in todos_plenos if not p.get("resumen_ia")]
    pleno_35 = next((p for p in todos_plenos if p["numero_acta"] == 35), None)

    print(f"Plenos sin resumen: {[p['numero_acta'] for p in plenos_sin_resumen]}")

    if do_all or args.only_resumenes:
        paso1_resumenes_plenos(client, plenos_sin_resumen)

    if do_all or args.only_puntos:
        # Procesar las actas que originalmente no tenían resumen
        plenos_a_rellenar = [p for p in todos_plenos if p["numero_acta"] in ACTAS_SIN_RESUMEN]
        paso2_resumenes_puntos(client, plenos_a_rellenar)

    if do_all or args.only_titles:
        if pleno_35:
            paso3_limpiar_titulos(client, pleno_35)
        else:
            print("Acta #35 no encontrada.")

    print("\nCorrecciones completadas.")


if __name__ == "__main__":
    main()
