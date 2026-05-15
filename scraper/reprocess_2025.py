"""Reprocesa todas las actas de 2025 con el nuevo extractor de votaciones."""
import sys
import subprocess
from pathlib import Path
import db

if __name__ == "__main__":
    municipio_id = db.get_municipio_id("San Sebastián")
    client = db.get_client()

    plenos = client.table("plenos").select("numero_acta").eq("municipio_id", municipio_id).gte("fecha", "2025-01-01").lt("fecha", "2026-01-01").order("numero_acta").execute()
    nums = sorted([p["numero_acta"] for p in plenos.data])
    print(f"Reprocesando {len(nums)} actas: {nums}\n")

    for i, num in enumerate(nums, 1):
        print(f"\n{'='*60}\n[{i}/{len(nums)}] Acta {num}\n{'='*60}")
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "run.py", "--year", "2025", "--reprocess", str(num)],
            cwd=Path(__file__).parent,
            capture_output=False,
        )
        if result.returncode != 0:
            print(f"  ERROR: acta {num} falló")

    print("\n✓ Reprocesado completado")
