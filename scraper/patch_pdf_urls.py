"""
patch_pdf_urls.py — Actualiza url_pdf_original para los plenos de San Sebastián
consultando el listado actual de la web de Donostia y emparejando por numero_acta.

Uso:
  cd actacivium/scraper
  python patch_pdf_urls.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from donostia import obtener_actas_disponibles
from import_actas import sb_get, sb_patch

print("=" * 55)
print("  Actualizando URLs de PDFs en la BD")
print("=" * 55)

# 1. Obtener listado real de PDFs de donostia.eus
print("\n[1/3] Consultando donostia.eus...")
try:
    actas_web = obtener_actas_disponibles()
except Exception as e:
    print(f"  Error al consultar donostia.eus: {e}")
    sys.exit(1)

url_por_numero: dict[int, str] = {a.numero_acta: a.url_pdf for a in actas_web}
print(f"  {len(url_por_numero)} actas encontradas en la web")

# 2. Obtener plenos con URL incorrecta o nula
print("\n[2/3] Obteniendo plenos de la BD...")
plenos = sb_get("plenos", {
    "select": "id,numero_acta,url_pdf_original",
    "order":  "numero_acta.asc",
})
print(f"  {len(plenos)} plenos en BD")

# 3. Actualizar los que tenemos URL
print("\n[3/3] Actualizando URLs...")
actualizados = 0
no_encontrados = []

for pleno in plenos:
    num = pleno["numero_acta"]
    url_actual = pleno.get("url_pdf_original") or ""

    if num in url_por_numero:
        nueva_url = url_por_numero[num]
        # Solo actualizar si es diferente o es la URL genérica/nula
        if nueva_url != url_actual:
            try:
                sb_patch("plenos", {"id": pleno["id"]}, {"url_pdf_original": nueva_url})
                print(f"  ✓ Pleno {num:>3}: {nueva_url}")
                actualizados += 1
            except Exception as e:
                print(f"  ✗ Pleno {num:>3}: Error — {e}")
    else:
        no_encontrados.append(num)

print(f"\n{'─'*55}")
print(f"  ✓ {actualizados} plenos actualizados")
if no_encontrados:
    print(f"  ⚠ Sin URL en web: plenos {no_encontrados}")
    print("    (pueden ser actas antiguas no publicadas en la web actual)")
print("=" * 55)
