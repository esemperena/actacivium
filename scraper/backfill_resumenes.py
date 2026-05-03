"""
Genera resumen_ia para puntos que no lo tienen, usando Claude CLI.

Uso:
  python backfill_resumenes.py                  # todos los puntos sin resumen
  python backfill_resumenes.py --pleno 39       # solo puntos del acta 39
  python backfill_resumenes.py --overwrite      # regenera también los resumenes malos
  python backfill_resumenes.py --fix-titles     # actualiza títulos truncados desde el cuerpo
"""
import argparse
import time
from db import get_client
from pdf_processor import generar_resumen_punto, PROMPT_RESUMEN_PLENO
import re, json, subprocess
from config import CLAUDE_CMD

_BAD_RESUMEN = re.compile(
    r"no (has|veo|tienes|incluiste)|¿puedes pegarlo|pégalo|estoy listo|"
    r"proporcion|no (se|se ha) inclui|parece que (has|no)|has compartido|"
    r"puedes compartir|¿en qué puedo|contexto previo|título de (un|una|el)|"
    r"¿puedes peg|pégalo aquí",
    re.I,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pleno", type=int, help="Número de acta a procesar")
    parser.add_argument("--overwrite", action="store_true",
                        help="Regenerar también resumenes que contienen respuestas incorrectas de Claude")
    parser.add_argument("--fix-titles", action="store_true",
                        help="Actualizar títulos truncados extrayéndolos del cuerpo del acta")
    args = parser.parse_args()

    client = get_client()

    q = client.table("plenos").select("id, numero_acta, texto_completo").eq("estado", "procesado")
    if args.pleno:
        q = q.eq("numero_acta", args.pleno)
    plenos = q.execute().data

    print(f"Procesando {len(plenos)} plenos…\n")

    for pleno in plenos:
        pleno_id = pleno["id"]
        num = pleno["numero_acta"]
        texto_pleno = pleno.get("texto_completo") or ""

        puntos = (
            client.table("puntos")
            .select("id, numero, titulo, resultado, unanimidad, resumen_ia")
            .eq("pleno_id", pleno_id)
            .order("numero")
            .execute()
            .data
        )

        pendientes = []
        for p in puntos:
            resumen = p.get("resumen_ia") or ""
            if not resumen:
                pendientes.append(p)
            elif args.overwrite and _BAD_RESUMEN.search(resumen):
                pendientes.append(p)

        if not pendientes:
            print(f"  Acta {num}: todos los puntos ya tienen resumen.")
            continue

        label = "puntos a regenerar" if args.overwrite else "puntos sin resumen"
        print(f"  Acta {num}: {len(pendientes)} {label}…")

        for p in pendientes:
            extracto = _extraer_fragmento(texto_pleno, p["numero"])

            titulo = p["titulo"] or ""

            resultado = p["resultado"] or "sin_votacion"
            texto_para_resumen = extracto if extracto else titulo
            resumen = generar_resumen_punto(titulo, resultado, texto_para_resumen)
            if resumen:
                client.table("puntos").update({"resumen_ia": resumen[:600]}).eq("id", p["id"]).execute()
                print(f"    [{p['numero']}] OK — {resumen[:80]}…")
            else:
                print(f"    [{p['numero']}] Sin respuesta de Claude.")
            time.sleep(1)

    print("\nFin del backfill.")


def _titulo_truncado(titulo: str) -> bool:
    """Heurística: título probablemente incompleto si termina en preposición/artículo."""
    return bool(re.search(r"\b(el|la|los|las|de|del|por|en|con|a|al|un|una|para|sobre)\s*$", titulo, re.I))


def _titulo_desde_cuerpo(texto: str, numero: int) -> str:
    """Extrae el título español desde el cuerpo del acta (más completo que el sumario)."""
    pat = re.compile(rf"\b{numero}\.-\s+(.{{10,}}?)(?:\n|$)")
    for m in pat.finditer(texto):
        linea = m.group(1).strip()
        # Formato bilingüe: "Basque N.- Spanish" → tomar la parte tras el segundo N.-
        doble = re.search(rf"\b{numero}\.-\s+(.+)", linea)
        titulo = doble.group(1).strip() if doble else linea
        titulo = re.sub(r"\s+\d{1,3}\s*$", "", titulo).strip()
        if len(titulo) >= 15:
            return titulo
    return ""


def _extraer_fragmento(texto: str, numero: int) -> str:
    """Extrae hasta 3000 chars del cuerpo del punto N en el texto del pleno."""
    pat = re.compile(rf"\b{numero}\.-\s+[A-ZÁÉÍÓÚÑÜ]")
    m = pat.search(texto)
    if not m:
        return ""
    inicio = m.start()
    # Buscar el siguiente punto o fin
    siguiente = re.search(rf"\b{numero + 1}\.-\s+[A-ZÁÉÍÓÚÑÜ]", texto[inicio + 10:])
    fin = inicio + 10 + siguiente.start() if siguiente else inicio + 4000
    return texto[inicio:fin][:3000]


if __name__ == "__main__":
    main()
