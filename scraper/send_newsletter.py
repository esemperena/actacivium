"""
Envía la newsletter de un pleno a los suscriptores de Brevo.

Uso directo:
  python send_newsletter.py <pleno_id>
  python send_newsletter.py <pleno_id> --test ejemplo@email.com
"""
import os
import sys
import httpx
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BREVO_API_KEY      = os.environ["BREVO_API_KEY"]
BREVO_LIST_ID      = int(os.environ.get("BREVO_LIST_ID", "6"))
BREVO_SENDER_EMAIL = os.environ["BREVO_SENDER_EMAIL"]
BREVO_SENDER_NAME  = os.environ.get("BREVO_SENDER_NAME", "Acta Civium")
WEB_BASE_URL       = os.environ.get("WEB_BASE_URL", "https://actacivium.netlify.app")

BREVO_API = "https://api.brevo.com/v3"
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "api-key": BREVO_API_KEY,
}

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

COLORES_RESULTADO = {
    "aprobado":          ("#1a6b3a", "#e6f4ec"),
    "aprobado_mayoria":  ("#2d7d4e", "#eaf5f0"),
    "rechazado":         ("#9b1c1c", "#fde8e8"),
    "retirado":          ("#6b7280", "#f3f4f6"),
    "sin_votacion":      ("#6b7280", "#f3f4f6"),
}

ETIQUETAS_RESULTADO = {
    "aprobado":         "Aprobado",
    "aprobado_mayoria": "Aprobado por mayoría",
    "rechazado":        "Rechazado",
    "retirado":         "Retirado",
    "sin_votacion":     "Sin votación",
}

ETIQUETAS_CATEGORIA = {
    "urbanismo":          "Urbanismo",
    "hacienda":           "Hacienda",
    "vivienda":           "Vivienda",
    "medio_ambiente":     "Medio ambiente",
    "servicios_sociales": "Servicios sociales",
    "movilidad":          "Movilidad",
    "educacion":          "Educación",
    "cultura":            "Cultura",
    "seguridad":          "Seguridad",
    "participacion":      "Participación ciudadana",
    "personal":           "Personal",
    "otros":              "Otros",
}


def _html_composicion(composicion: list[dict]) -> str:
    """Barra horizontal coloreada por partido + leyenda. Sin imágenes, compatible con todos los clientes de email."""
    if not composicion:
        return ""
    total = sum(p["concejales"] for p in composicion)
    if not total:
        return ""

    # Celdas de la barra proporcional
    celdas_barra = []
    for p in composicion:
        pct = round(p["concejales"] / total * 100)
        celdas_barra.append(
            f'<td width="{pct}%" style="padding:0;background:{p["color"]};height:20px;"></td>'
        )

    # Filas de leyenda
    filas_leyenda = []
    for p in composicion:
        pct = round(p["concejales"] / total * 100)
        filas_leyenda.append(
            f'<tr>'
            f'<td style="padding:5px 10px 5px 0;vertical-align:middle;">'
            f'  <div style="width:11px;height:11px;border-radius:50%;background:{p["color"]};"></div>'
            f'</td>'
            f'<td style="padding:5px 16px 5px 0;font-size:12px;font-weight:700;color:#111827;vertical-align:middle;white-space:nowrap;">'
            f'  {p["siglas"]}'
            f'</td>'
            f'<td style="padding:5px 16px 5px 0;font-size:12px;color:#374151;vertical-align:middle;white-space:nowrap;">'
            f'  {p["concejales"]} escaños'
            f'</td>'
            f'<td style="padding:5px 0;font-size:11px;color:#9ca3af;vertical-align:middle;">'
            f'  {pct}%'
            f'</td>'
            f'</tr>'
        )

    return f"""
    <div style="margin-bottom:28px;">
      <p style="margin:0 0 14px;font-size:11px;font-weight:700;letter-spacing:.1em;
                text-transform:uppercase;color:#6b7280;">Composición del pleno</p>

      <!-- Barra proporcional -->
      <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:16px;">
        <tr>{"".join(celdas_barra)}</tr>
      </table>

      <!-- Leyenda -->
      <table cellpadding="0" cellspacing="0">
        {"".join(filas_leyenda)}
      </table>
    </div>"""


# ── Consulta de datos ────────────────────────────────────────────────────────

def obtener_datos_pleno(pleno_id: str) -> dict | None:
    from db import get_client
    client = get_client()

    r = client.table("plenos").select(
        "id, fecha, tipo_sesion, resumen_ia, n_puntos, n_asistentes, n_ausentes"
    ).eq("id", pleno_id).single().execute()
    if not r.data:
        return None
    pleno = r.data

    from config import NEWSLETTER_MIN_RELEVANCIA
    r_puntos = client.table("puntos").select(
        "numero, titulo, categoria, tipo, resultado, resumen_ia, relevancia_social"
    ).eq("pleno_id", pleno_id) \
     .gte("relevancia_social", NEWSLETTER_MIN_RELEVANCIA) \
     .not_.in_("tipo", ["dar_cuenta", "otro"]) \
     .order("relevancia_social", desc=True) \
     .limit(8).execute()

    # Usar v_plenos igual que la web: total_puntos y aprobados/rechazados calculados por la vista
    r_vpleno = client.from_("v_plenos").select(
        "total_puntos, aprobados, rechazados"
    ).eq("id", pleno_id).single().execute()

    n_resolutivos = r_vpleno.data.get("total_puntos") or 0
    aprobados     = r_vpleno.data.get("aprobados") or 0
    rechazados    = r_vpleno.data.get("rechazados") or 0

    # Concejales presentes por partido (máximo de votos emitidos en cualquier punto)
    r_pts = client.table("puntos").select("id").eq("pleno_id", pleno_id).execute()
    punto_ids = [p["id"] for p in (r_pts.data or [])]

    partidos_presentes = []
    if punto_ids:
        r_vot = client.table("votaciones").select(
            "partido_id, votos_favor, votos_contra, abstenciones, partidos(siglas, color_hex)"
        ).in_("punto_id", punto_ids).execute()

        # Acumulamos el máximo de concejales que votaron por partido en cualquier punto
        maximos: dict[str, dict] = {}
        for row in (r_vot.data or []):
            p = row.get("partidos") or {}
            siglas = p.get("siglas", "")
            color  = p.get("color_hex", "#888888")
            if not siglas:
                continue
            total_votos = (row.get("votos_favor") or 0) + \
                          (row.get("votos_contra") or 0) + \
                          (row.get("abstenciones") or 0)
            if siglas not in maximos or total_votos > maximos[siglas]["concejales"]:
                maximos[siglas] = {"siglas": siglas, "color": color, "concejales": total_votos}

        partidos_presentes = sorted(maximos.values(), key=lambda x: -x["concejales"])

    # Composición del pleno: escaños por partido (máximo de votos en cualquier punto del histórico)
    r_all_vot = client.table("votaciones").select(
        "votos_favor, votos_contra, abstenciones, partidos(siglas, color_hex)"
    ).execute()
    maximos_global: dict[str, dict] = {}
    for row in (r_all_vot.data or []):
        p = row.get("partidos") or {}
        siglas = p.get("siglas", "")
        if not siglas:
            continue
        total_v = (row.get("votos_favor") or 0) + \
                  (row.get("votos_contra") or 0) + \
                  (row.get("abstenciones") or 0)
        if siglas not in maximos_global or total_v > maximos_global[siglas]["concejales"]:
            maximos_global[siglas] = {
                "siglas": siglas,
                "color": p.get("color_hex", "#888888"),
                "concejales": total_v,
            }
    composicion = sorted(maximos_global.values(), key=lambda x: -x["concejales"])

    return {
        "pleno": pleno,
        "n_resolutivos": n_resolutivos,
        "puntos": r_puntos.data or [],
        "aprobados": aprobados,
        "rechazados": rechazados,
        "partidos_presentes": partidos_presentes,
        "composicion": composicion,
    }


# ── Helpers HTML ─────────────────────────────────────────────────────────────

def _fecha_larga(fecha_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(fecha_iso)
        return f"{dt.day} de {MESES[dt.month]} de {dt.year}"
    except Exception:
        return fecha_iso


def _badge_resultado(resultado: str) -> str:
    color_texto, color_fondo = COLORES_RESULTADO.get(resultado, ("#6b7280", "#f3f4f6"))
    etiqueta = ETIQUETAS_RESULTADO.get(resultado, resultado)
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:4px;'
        f'font-size:11px;font-weight:600;letter-spacing:.04em;'
        f'background:{color_fondo};color:{color_texto};">'
        f'{etiqueta}</span>'
    )


def _badge_categoria(categoria: str) -> str:
    etiqueta = ETIQUETAS_CATEGORIA.get(categoria, categoria or "Otros")
    return (
        f'<span style="font-size:10px;font-weight:700;letter-spacing:.08em;'
        f'text-transform:uppercase;color:#2d6a4f;">{etiqueta}</span>'
    )


def _formatear_resumen(resumen: str) -> str:
    """Divide el resumen en párrafos cortos, uno por idea."""
    if not resumen:
        return ""
    # Normalizar saltos de línea y separar por punto final
    texto = resumen.replace("\n\n", "\n").replace("\r", "")
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]

    # Si ya viene en varias líneas, respetarlas; si es un bloque, partir por ". "
    if len(lineas) <= 2:
        frases = []
        for linea in lineas:
            partes = linea.split(". ")
            frases.extend([p.strip() for p in partes if p.strip()])
        lineas = frases

    parrafos = []
    for frase in lineas:
        if not frase.endswith("."):
            frase += "."
        parrafos.append(
            f'<p style="margin:0 0 12px;font-size:15px;color:#374151;line-height:1.75;">'
            f'{frase}</p>'
        )
    return "".join(parrafos)


def _html_asistencia(pleno: dict, partidos: list) -> str:
    n_presentes = pleno.get("n_asistentes") or 0
    n_ausentes  = pleno.get("n_ausentes") or 0
    n_total     = n_presentes + n_ausentes
    pct         = int(n_presentes / n_total * 100) if n_total else 0

    # Barra de progreso de asistencia total
    barra_presente = f'width:{pct}%;background:#2d6a4f;'
    barra_ausente  = f'width:{100 - pct}%;background:#e5e7eb;'

    # Chips de partidos con concejales
    chips_html = ""
    if partidos:
        chips = []
        for p in partidos:
            concejales = p.get("concejales", 0)
            count_str = f'{concejales} conc.' if concejales else ""
            chips.append(
                f'<table cellpadding="0" cellspacing="0" style="display:inline-table;'
                f'margin:5px 8px 5px 0;background:#ffffff;border:1px solid #e5e7eb;border-radius:6px;">'
                f'<tr>'
                f'<td style="padding:7px 8px 7px 10px;vertical-align:middle;">'
                f'<div style="width:11px;height:11px;border-radius:50%;background:{p["color"]};"></div>'
                f'</td>'
                f'<td style="padding:7px 4px 7px 5px;vertical-align:middle;'
                f'font-size:12px;font-weight:700;color:#111827;white-space:nowrap;line-height:1;">'
                f'{p["siglas"]}</td>'
                f'<td style="padding:7px 10px 7px 5px;vertical-align:middle;'
                f'font-size:11px;color:#6b7280;white-space:nowrap;line-height:1;">'
                f'{count_str}</td>'
                f'</tr></table>'
            )
        chips_html = f'<div style="margin-top:16px;">{"".join(chips)}</div>'

    return f"""
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:20px 24px;margin-bottom:28px;">
      <p style="margin:0 0 14px;font-size:11px;font-weight:700;letter-spacing:.1em;
                text-transform:uppercase;color:#6b7280;">Asistencia al pleno</p>

      <!-- Barra -->
      <div style="border-radius:4px;overflow:hidden;height:8px;background:#e5e7eb;margin-bottom:14px;">
        <div style="width:{pct}%;height:8px;background:#2d6a4f;"></div>
      </div>

      <!-- Números -->
      <table cellpadding="0" cellspacing="0" width="100%">
        <tr>
          <td style="padding:0 24px 0 0;white-space:nowrap;">
            <span style="font-size:20px;font-weight:700;color:#111827;">{n_presentes}</span>
            <span style="font-size:13px;color:#6b7280;margin-left:5px;">presentes</span>
          </td>
          <td style="padding:0 24px 0 0;white-space:nowrap;">
            <span style="font-size:20px;font-weight:700;color:#111827;">{n_ausentes}</span>
            <span style="font-size:13px;color:#6b7280;margin-left:5px;">ausentes</span>
          </td>
          <td style="padding:0;white-space:nowrap;">
            <span style="font-size:13px;color:#9ca3af;">de {n_total} concejales</span>
          </td>
        </tr>
      </table>

      {chips_html}
    </div>"""


def _html_punto(punto: dict) -> str:
    titulo   = punto.get("titulo", "")
    resumen  = punto.get("resumen_ia") or ""
    categoria = punto.get("categoria") or "otros"
    resultado = punto.get("resultado") or "sin_votacion"

    return f"""
    <div style="border-top:1px solid #e5e7eb;padding:20px 0;">
      <div style="margin-bottom:8px;">
        {_badge_categoria(categoria)}&nbsp;&nbsp;{_badge_resultado(resultado)}
      </div>
      <p style="margin:0 0 8px;font-family:Georgia,'Times New Roman',serif;
                font-size:17px;font-weight:700;color:#111827;line-height:1.35;">
        {titulo}
      </p>
      {f'<p style="margin:0;font-size:14px;color:#4b5563;line-height:1.65;">{resumen}</p>' if resumen else ''}
    </div>"""


# ── Generador HTML principal ─────────────────────────────────────────────────

# Gmail y la mayoría de clientes de email bloquean data URIs.
# Solo funcionan URLs públicas. El favicon.ico está en Netlify.
LOGO_HTML = f'<img src="{WEB_BASE_URL}/favicon.ico" width="48" height="48" alt="Acta Civium" style="display:block;margin:0 auto;border-radius:8px;">'


def generar_html(datos: dict) -> str:
    pleno      = datos["pleno"]
    puntos     = datos["puntos"]
    aprobados  = datos["aprobados"]
    rechazados = datos["rechazados"]
    partidos   = datos.get("partidos_presentes", [])

    fecha_fmt  = _fecha_larga(pleno.get("fecha", ""))
    tipo       = pleno.get("tipo_sesion", "ordinaria").capitalize()
    resumen    = pleno.get("resumen_ia") or ""
    n_puntos   = pleno.get("n_puntos", 0)
    pleno_id   = pleno["id"]
    url_pleno  = f"{WEB_BASE_URL}/acta/{pleno_id}"

    composicion     = datos.get("composicion", [])
    n_puntos        = datos.get("n_resolutivos", n_puntos)
    sin_votar       = n_puntos - aprobados - rechazados
    resumen_html    = _formatear_resumen(resumen)
    composicion_html = _html_composicion(composicion)
    asistencia_html = _html_asistencia(pleno, partidos)
    puntos_html     = "".join(_html_punto(p) for p in puntos)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Pleno {tipo} — {fecha_fmt}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:620px;margin:32px auto 48px;">

  <!-- Cabecera -->
  <div style="background:#111827;border-radius:8px 8px 0 0;padding:36px 32px;text-align:center;">
    {LOGO_HTML}
    <h1 style="margin:14px 0 4px;font-family:Georgia,'Times New Roman',serif;
               font-size:28px;font-weight:700;color:#ffffff;letter-spacing:-.01em;">
      Acta Civium
    </h1>
    <p style="margin:0;font-size:13px;color:#9ca3af;letter-spacing:.02em;">
      El pleno municipal, explicado
    </p>
  </div>

  <!-- Subheader: fecha y tipo de pleno -->
  <div style="background:#1f2937;padding:12px 32px;text-align:center;border-bottom:1px solid #374151;">
    <p style="margin:0;font-size:13px;color:#d1d5db;">
      <span style="color:#6ee7b7;font-weight:600;text-transform:uppercase;
                   letter-spacing:.08em;font-size:11px;">San Sebastián</span>
      &nbsp;·&nbsp; Pleno {tipo} &nbsp;·&nbsp; {fecha_fmt}
    </p>
  </div>

  <!-- Intro -->
  <div style="background:#f9fafb;padding:14px 32px;border-bottom:1px solid #e5e7eb;text-align:center;">
    <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.6;">
      El Ayuntamiento se reunió en pleno {tipo.lower()} el {fecha_fmt}.
      Aquí tienes lo que se debatió, qué se aprobó y cómo votó cada grupo.
    </p>
  </div>

  <!-- Cuerpo -->
  <div style="background:#ffffff;padding:32px;border-radius:0 0 8px 8px;border:1px solid #e5e7eb;border-top:none;">

    <!-- Stats: puntos, aprobados, rechazados -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;border:1px solid #e5e7eb;border-radius:6px;overflow:hidden;">
      <tr>
        <td width="33%" style="padding:18px 12px;text-align:center;border-right:1px solid #e5e7eb;">
          <div style="font-size:28px;font-weight:700;color:#111827;line-height:1;">{n_puntos}</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.07em;margin-top:6px;">Puntos</div>
        </td>
        <td width="33%" style="padding:18px 12px;text-align:center;border-right:1px solid #e5e7eb;">
          <div style="font-size:28px;font-weight:700;color:#1a6b3a;line-height:1;">{aprobados}</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.07em;margin-top:6px;">Aprobados</div>
        </td>
        <td width="33%" style="padding:18px 12px;text-align:center;">
          <div style="font-size:28px;font-weight:700;color:#9b1c1c;line-height:1;">{rechazados}</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.07em;margin-top:6px;">Rechazados</div>
        </td>
      </tr>
    </table>

    <!-- Composición del pleno -->
    {composicion_html}

    <!-- Banner asistencia -->
    {asistencia_html}

    <!-- Resumen del pleno -->
    {f'''<div style="border-left:3px solid #2d6a4f;padding-left:16px;margin-bottom:32px;">
      <p style="margin:0 0 10px;font-size:11px;font-weight:700;letter-spacing:.1em;
                text-transform:uppercase;color:#2d6a4f;">Resumen del pleno</p>
      {resumen_html}
    </div>''' if resumen_html else ''}

    <!-- Puntos destacados -->
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;
              text-transform:uppercase;color:#2d6a4f;">Lo más relevante</p>
    {puntos_html if puntos_html else '<p style="color:#6b7280;font-size:14px;margin:16px 0;">No hay puntos destacados en este pleno.</p>'}

    <!-- CTA -->
    <div style="text-align:center;margin-top:36px;">
      <a href="{url_pleno}"
         style="display:inline-block;padding:13px 32px;background:#111827;color:#ffffff;
                font-size:14px;font-weight:600;text-decoration:none;border-radius:6px;
                letter-spacing:.02em;">
        Ver acta completa &rarr;
      </a>
    </div>

  </div>

  <!-- Footer -->
  <div style="padding:20px 32px;text-align:center;">
    <p style="margin:0 0 6px;font-size:12px;color:#9ca3af;">
      <a href="{WEB_BASE_URL}" style="color:#6b7280;text-decoration:none;">actacivium.netlify.app</a>
      &nbsp;&middot;&nbsp; Datos públicos del Ayuntamiento de San Sebastián
    </p>
    <p style="margin:0;font-size:11px;color:#d1d5db;">
      <a href="{{{{ unsubscribe }}}}" style="color:#d1d5db;text-decoration:underline;">Darse de baja</a>
    </p>
  </div>

</div>
</body>
</html>"""


# ── Envío via Brevo ──────────────────────────────────────────────────────────

def _crear_campana(asunto: str, html: str, lista_ids: list[int]) -> int:
    r = httpx.post(
        f"{BREVO_API}/emailCampaigns",
        headers=HEADERS,
        json={
            "name": f"Acta Civium — {asunto}",
            "subject": asunto,
            "sender": {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
            "type": "classic",
            "htmlContent": html,
            "recipients": {"listIds": lista_ids},
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]


def _crear_y_enviar_campana(asunto: str, html: str, lista_ids: list[int]) -> bool:
    campaign_id = _crear_campana(asunto, html, lista_ids)
    r = httpx.post(
        f"{BREVO_API}/emailCampaigns/{campaign_id}/sendNow",
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    return True


def _enviar_test(asunto: str, html: str, email_destino: str) -> bool:
    campaign_id = _crear_campana(asunto, html, [BREVO_LIST_ID])
    r = httpx.post(
        f"{BREVO_API}/emailCampaigns/{campaign_id}/sendTest",
        headers=HEADERS,
        json={"emailTo": [email_destino]},
        timeout=30,
    )
    r.raise_for_status()
    return True


# ── Punto de entrada público ─────────────────────────────────────────────────

def enviar_newsletter(pleno_id: str, test_email: str | None = None) -> bool:
    datos = obtener_datos_pleno(pleno_id)
    if not datos:
        print(f"    [!] Newsletter: pleno {pleno_id} no encontrado en BD")
        return False

    fecha_fmt = _fecha_larga(datos["pleno"].get("fecha", ""))
    tipo      = datos["pleno"].get("tipo_sesion", "ordinaria").capitalize()
    asunto    = f"Pleno {tipo} de San Sebastian — {fecha_fmt}"
    html      = generar_html(datos)

    if test_email:
        _enviar_test(asunto, html, test_email)
        print(f"    OK Newsletter de prueba enviada a {test_email}")
    else:
        _crear_y_enviar_campana(asunto, html, [BREVO_LIST_ID])
        print(f"    OK Newsletter enviada (lista {BREVO_LIST_ID}, {len(datos['puntos'])} puntos)")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enviar newsletter de un pleno")
    parser.add_argument("pleno_id", help="UUID del pleno en Supabase")
    parser.add_argument("--test", metavar="EMAIL", help="Enviar solo a este email (modo prueba)")
    args = parser.parse_args()

    ok = enviar_newsletter(args.pleno_id, test_email=args.test)
    sys.exit(0 if ok else 1)
