"""Debug del parser del Congreso."""
import sys, pathlib, types, re

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

config = types.ModuleType("config")
config.CLAUDE_CMD = "claude"
config.PDF_MAX_PAGES_FOR_SUMMARY = 60
sys.modules["config"] = config

import pdf_processor_congreso as p

pdf_path = pathlib.Path("C:/Users/EnaitzSemperena/AppData/Local/Temp/DSCD-15-PL-183.PDF")
texto = p.extraer_texto(pdf_path)

print("=== PRIMEROS 600 CHARS DEL TEXTO LIMPIO ===")
print(repr(texto[:600]))
print()

print("=== BUSCAR 'SUMARIO' EN TEXTO ===")
m = re.search(r"\bSUMARIO\b", texto, re.I)
print("Encontrado:", m)
if m:
    print("Posición:", m.start())
    print("Contexto:", repr(texto[m.start()-20:m.start()+200]))
print()

print("=== BUSCAR 'celebrada el' EN TEXTO ===")
m = re.search(r"celebrada el\s+(\S.*?)(\n|$)", texto, re.I)
print("Encontrado:", m)
if m:
    print("Match:", repr(m.group(0)))
print()

print("=== BUSCAR 'PRESIDENCIA' EN TEXTO ===")
m = re.search(r"PRESIDENCIA", texto[:500])
print("Encontrado:", m)
if m:
    print("Contexto:", repr(texto[m.start():m.start()+100]))
print()

print("=== BUSCAR em-dash '—' EN TEXTO ===")
pos = texto.find("—")
print("Primera posición:", pos)
if pos > 0:
    print("Contexto:", repr(texto[pos-10:pos+80]))

print()
print("=== BUSCAR 'Sometida a votación' ===")
m = re.search(r"Sometida a votaci", texto)
print("Encontrado:", m)
if m:
    print("Contexto:", repr(texto[m.start():m.start()+200]))
