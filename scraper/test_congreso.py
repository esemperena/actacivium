"""Script de validación del parser del Congreso. Ejecutar manualmente."""
import sys, pathlib, types

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

config = types.ModuleType("config")
config.CLAUDE_CMD = "claude"
config.PDF_MAX_PAGES_FOR_SUMMARY = 60
sys.modules["config"] = config

import pdf_processor_congreso as p

pdf_path = pathlib.Path("C:/Users/EnaitzSemperena/AppData/Local/Temp/DSCD-15-PL-183.PDF")
texto = p.extraer_texto(pdf_path)

print("=== METADATOS ===")
meta = p.extraer_metadatos(texto)
for k, v in meta.items():
    print(f"  {k}: {v}")

print("\n=== PUNTOS DEL SUMARIO ===")
puntos = p.extraer_puntos_sumario(texto)
print(f"  Total puntos extraídos: {len(puntos)}")
for pt in puntos:
    linea = f"  [{pt['numero']}] tipo={pt['tipo_seccion']} | exp={pt['expediente']}"
    print(linea)
    print(f"       {pt['titulo'][:90]}")
    if pt.get("grupo_proponente_raw"):
        print(f"       grupo: {pt['grupo_proponente_raw']}")

print("\n=== VOTACIONES ===")
votes = p.extraer_votaciones_por_punto(texto)
print(f"  Total votaciones extraídas: {len(votes)}")
for num, v in sorted(votes.items()):
    print(f"  Punto {num}: {v['resultado']} | favor={v['total_favor']} contra={v['total_contra']} abst={v['total_abstenciones']}")

print("\n=== CLASIFICACIÓN PUNTOS ===")
for pt in puntos:
    cat = p.clasificar_categoria(pt["titulo"])
    tipo = pt["tipo_seccion"] or p.clasificar_tipo(pt["titulo"])
    print(f"  [{pt['numero']}] cat={cat} tipo={tipo}")
