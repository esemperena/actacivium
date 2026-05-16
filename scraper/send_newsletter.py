"""
Envía la newsletter de un pleno a los suscriptores de Brevo.

Diseño alineado con actacivium.netlify.app:
  - Tipos:  Playfair Display (serif, fallback Georgia) + DM Sans (body)
  - Color:  fondo crema #f4f5f0 · acento bosque #1f6a47 · tinta #1c1f24
  - HTML email-safe: <table> layout, estilos inline, sin SVG, sin oklch.

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

# ── Sistema visual (HEX, equivalencias del oklch de la web) ─────────────────
COLOR_BG       = "#ebece8"   # body
COLOR_CARD     = "#fafaf6"   # email card
COLOR_BG_SOFT  = "#ffffff"   # bloques sobre la card
COLOR_BORDER   = "#dde0db"
COLOR_RULE     = "#e3e5df"
COLOR_RULE_2   = "#eceee9"
COLOR_INK      = "#1c1f24"
COLOR_INK_MUTED= "#52555c"
COLOR_INK_SOFT = "#8b8e94"
COLOR_ACCENT   = "#1f6a47"   # forest green (oklch 42% 0.13 158)
COLOR_ACCENT_BG= "#f3f7f4"
COLOR_GREEN    = "#1c6041"
COLOR_GREEN_BG = "#e6f0e9"
COLOR_RED      = "#aa3326"
COLOR_RED_BG   = "#f7e4e1"

FONT_SERIF = "'Playfair Display',Georgia,serif"
FONT_SANS  = "'DM Sans',Helvetica,Arial,sans-serif"

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# Resultado → (color texto, color fondo, etiqueta, símbolo)
RESULTADOS = {
    "aprobado":          (COLOR_GREEN,    COLOR_GREEN_BG, "Aprobado",            "✓"),
    "aprobado_mayoria":  (COLOR_GREEN,    COLOR_GREEN_BG, "Aprobado por mayoría","✓"),
    "rechazado":         (COLOR_RED,      COLOR_RED_BG,   "Rechazado",           "✕"),
    "retirado":          (COLOR_INK_SOFT, "#f3f4f0",      "Retirado",            "·"),
    "sin_votacion":      (COLOR_INK_SOFT, "#f3f4f0",      "Sin votación",        "·"),
}

# Categoría → (color texto, color fondo, etiqueta)
# Reproduce el sistema de badges de global.css: chroma unificado, hue por tema.
CATEGORIAS = {
    "vivienda":           ("#23527a", "#e0eef7", "Vivienda"),
    "urbanismo":          ("#1a5470", "#dfeaf2", "Urbanismo"),
    "hacienda":           ("#6b4a14", "#f1e8d4", "Hacienda"),
    "medio_ambiente":     ("#1f5e3a", "#dfeee5", "Medio ambiente"),
    "servicios_sociales": ("#5a2a72", "#ece0f0", "Servicios sociales"),
    "movilidad":          ("#1f4e7a", "#dfe9f4", "Movilidad"),
    "educacion":          ("#2a3e7a", "#e0e5f4", "Educación"),
    "cultura":            ("#5e2c6c", "#ecdef0", "Cultura"),
    "seguridad":          ("#33405b", "#e2e6ee", "Seguridad"),
    "participacion":      ("#1f5e3a", "#dfeee5", "Participación"),
    "derechos":           ("#6c2e54", "#efdfe8", "Derechos"),
    "personal":           ("#404040", "#e8e8e8", "Personal"),
    "otros":              ("#5a5e64", "#e8e9ea", "Otros"),
}


# ── Helpers de formato ───────────────────────────────────────────────────────

def _fecha_larga(fecha_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(fecha_iso)
        return f"{dt.day} de {MESES[dt.month]} de {dt.year}"
    except Exception:
        return fecha_iso


def _badge_categoria(categoria: str) -> str:
    color, bg, etiqueta = CATEGORIAS.get(categoria or "otros", CATEGORIAS["otros"])
    return (
        f'<span style="display:inline-block;font-size:10px;font-weight:700;'
        f'letter-spacing:0.1em;text-transform:uppercase;color:{color};'
        f'background:{bg};padding:3px 8px;border-radius:3px;">{etiqueta}</span>'
    )


def _badge_resultado(resultado: str) -> str:
    color, bg, etiqueta, simbolo = RESULTADOS.get(
        resultado or "sin_votacion", RESULTADOS["sin_votacion"]
    )
    return (
        f'<span style="display:inline-block;font-size:10px;font-weight:700;'
        f'letter-spacing:0.1em;text-transform:uppercase;color:{color};'
        f'background:{bg};padding:3px 8px;border-radius:3px;">{simbolo} {etiqueta}</span>'
    )


def _formatear_resumen(resumen: str) -> str:
    """Limpia el resumen en un párrafo único, legible."""
    if not resumen:
        return ""
    texto = " ".join(resumen.replace("\r", "").split())
    return (
        f'<p style="margin:0;font-family:{FONT_SANS};font-size:14.5px;'
        f'line-height:1.7;color:#3a3e44;">{texto}</p>'
    )


# ── Bloques de plantilla ─────────────────────────────────────────────────────

def _html_header(numero: int, ciudad: str) -> str:
    return f"""
    <tr>
      <td style="padding:30px 36px 22px;border-bottom:1px solid {COLOR_RULE};">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="font-family:{FONT_SERIF};font-size:19px;font-weight:700;letter-spacing:-0.02em;color:{COLOR_INK};line-height:1;">Acta Civium</td>
            <td align="right" style="font-family:{FONT_SANS};font-size:10.5px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#7a8a7d;">Núm. {numero} · {ciudad}</td>
          </tr>
        </table>
      </td>
    </tr>"""


def _html_masthead(tipo: str, fecha_fmt: str) -> str:
    return f"""
    <tr>
      <td style="padding:44px 36px 12px;">
        <p style="margin:0 0 18px;font-family:{FONT_SANS};font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{COLOR_ACCENT};">
          <span style="display:inline-block;width:5px;height:5px;background:{COLOR_ACCENT};border-radius:50%;vertical-align:middle;margin-right:8px;opacity:.6;"></span>Pleno {tipo} · {fecha_fmt}
        </p>
      </td>
    </tr>"""


def _html_stats(n_puntos: int, aprobados: int, rechazados: int) -> str:
    return f"""
    <tr>
      <td style="padding:28px 36px 8px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{COLOR_BG_SOFT};border:1px solid {COLOR_RULE};border-radius:6px;">
          <tr>
            <td width="33%" align="center" style="padding:20px 12px;border-right:1px solid {COLOR_RULE_2};">
              <div style="font-family:{FONT_SERIF};font-size:32px;font-weight:700;color:{COLOR_INK};line-height:1;letter-spacing:-0.02em;">{n_puntos}</div>
              <div style="margin-top:8px;font-family:{FONT_SANS};font-size:10.5px;font-weight:600;color:{COLOR_INK_SOFT};text-transform:uppercase;letter-spacing:0.1em;">Puntos</div>
            </td>
            <td width="33%" align="center" style="padding:20px 12px;border-right:1px solid {COLOR_RULE_2};">
              <div style="font-family:{FONT_SERIF};font-size:32px;font-weight:700;color:{COLOR_GREEN};line-height:1;letter-spacing:-0.02em;">{aprobados}</div>
              <div style="margin-top:8px;font-family:{FONT_SANS};font-size:10.5px;font-weight:600;color:{COLOR_INK_SOFT};text-transform:uppercase;letter-spacing:0.1em;">Aprobados</div>
            </td>
            <td width="33%" align="center" style="padding:20px 12px;">
              <div style="font-family:{FONT_SERIF};font-size:32px;font-weight:700;color:{COLOR_RED};line-height:1;letter-spacing:-0.02em;">{rechazados}</div>
              <div style="margin-top:8px;font-family:{FONT_SANS};font-size:10.5px;font-weight:600;color:{COLOR_INK_SOFT};text-transform:uppercase;letter-spacing:0.1em;">Rechazados</div>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _html_composicion(composicion: list[dict]) -> str:
    if not composicion:
        return ""
    total = sum(p["concejales"] for p in composicion)
    if not total:
        return ""

    celdas = "".join(
        f'<td width="{round(p["concejales"]/total*100)}%" style="background:{p["color"]};height:14px;font-size:0;line-height:0;">&nbsp;</td>'
        for p in composicion
    )
    leyenda = "".join(
        f'<td style="padding:6px 14px 6px 0;font-family:{FONT_SANS};font-size:12px;color:{COLOR_INK};white-space:nowrap;vertical-align:middle;">'
        f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{p["color"]};vertical-align:middle;margin-right:6px;"></span>'
        f'<strong style="font-weight:600;">{p["siglas"]}</strong> '
        f'<span style="color:{COLOR_INK_SOFT};">· {p["concejales"]}</span>'
        f'</td>'
        for p in composicion
    )
    return f"""
    <tr>
      <td style="padding:24px 36px 8px;">
        <p style="margin:0 0 14px;font-family:{FONT_SANS};font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{COLOR_INK_SOFT};">Composición del pleno</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;border-radius:3px;overflow:hidden;">
          <tr>{celdas}</tr>
        </table>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:14px;">
          <tr>{leyenda}</tr>
        </table>
      </td>
    </tr>"""


def _html_asistencia(pleno: dict) -> str:
    n_presentes = pleno.get("n_asistentes") or 0
    n_ausentes  = pleno.get("n_ausentes") or 0
    n_total     = n_presentes + n_ausentes
    if not n_total:
        return ""
    pct = int(n_presentes / n_total * 100)
    return f"""
    <tr>
      <td style="padding:24px 36px 8px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{COLOR_BG_SOFT};border:1px solid {COLOR_RULE};border-radius:6px;">
          <tr>
            <td style="padding:18px 22px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-family:{FONT_SANS};font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{COLOR_INK_SOFT};">Asistencia</td>
                  <td align="right" style="font-family:{FONT_SANS};font-size:12px;color:{COLOR_INK_SOFT};">
                    <strong style="color:{COLOR_INK};font-weight:600;">{n_presentes}</strong> de {n_total} concejales · <strong style="color:{COLOR_INK};font-weight:600;">{pct}%</strong>
                  </td>
                </tr>
              </table>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px;border-collapse:separate;border-radius:99px;overflow:hidden;">
                <tr>
                  <td width="{pct}%" style="background:{COLOR_ACCENT};height:6px;font-size:0;line-height:0;">&nbsp;</td>
                  <td width="{100-pct}%" style="background:{COLOR_RULE};height:6px;font-size:0;line-height:0;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _html_resumen(resumen_html: str) -> str:
    if not resumen_html:
        return ""
    return f"""
    <tr>
      <td style="padding:28px 36px 4px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="padding:4px 0 4px 18px;border-left:3px solid {COLOR_ACCENT};">
              <p style="margin:0 0 8px;font-family:{FONT_SANS};font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{COLOR_ACCENT};">Resumen del pleno</p>
              {resumen_html}
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _html_punto(punto: dict) -> str:
    titulo    = punto.get("titulo", "")
    resumen   = punto.get("resumen_ia") or ""
    categoria = punto.get("categoria") or "otros"
    resultado = punto.get("resultado") or "sin_votacion"
    return f"""
    <tr>
      <td style="padding:0 36px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr><td style="border-top:1px solid {COLOR_RULE};height:1px;font-size:0;line-height:0;">&nbsp;</td></tr>
          <tr>
            <td style="padding:18px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom:8px;">
                <tr>
                  <td style="padding-right:8px;">{_badge_categoria(categoria)}</td>
                  <td>{_badge_resultado(resultado)}</td>
                </tr>
              </table>
              <p style="margin:0 0 6px;font-family:{FONT_SERIF};font-size:18px;font-weight:600;line-height:1.3;letter-spacing:-0.015em;color:{COLOR_INK};">{titulo}</p>
              {f'<p style="margin:0;font-family:{FONT_SANS};font-size:13.5px;line-height:1.65;color:{COLOR_INK_MUTED};">{resumen}</p>' if resumen else ''}
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _html_cta(url_pleno: str, ciudad: str) -> str:
    return f"""
    <tr>
      <td align="center" style="padding:36px 36px 8px;">
        <a href="{url_pleno}" style="display:inline-block;font-family:{FONT_SANS};font-size:14px;font-weight:600;color:#ffffff;background:{COLOR_ACCENT};text-decoration:none;padding:13px 30px;border-radius:6px;letter-spacing:0.01em;">Leer el acta completa →</a>
      </td>
    </tr>
    <tr>
      <td align="center" style="padding:20px 36px 0;">
        <p style="margin:0;font-family:{FONT_SANS};font-size:11.5px;color:{COLOR_INK_SOFT};line-height:1.5;">
          Resúmenes generados automáticamente a partir del acta oficial.<br>
          En caso de duda, prevalece el texto original.
        </p>
      </td>
    </tr>"""


def _html_footer(ciudad: str) -> str:
    return f"""
    <tr>
      <td style="padding:36px 36px 32px;">
        <div style="border-top:1px solid {COLOR_RULE};padding-top:22px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="font-family:{FONT_SERIF};font-size:14px;font-weight:700;letter-spacing:-0.02em;color:{COLOR_INK};">Acta Civium</td>
              <td align="right" style="font-family:{FONT_SANS};font-size:11px;color:{COLOR_INK_SOFT};">actacivium.netlify.app</td>
            </tr>
          </table>
          <p style="margin:14px 0 0;font-family:{FONT_SANS};font-size:11.5px;line-height:1.6;color:{COLOR_INK_SOFT};">
            Datos públicos del Ayuntamiento de {ciudad}, procesados de forma independiente.
            ·
            <a href="{{{{ unsubscribe }}}}" style="color:{COLOR_INK_SOFT};text-decoration:underline;">Darme de baja</a>
          </p>
        </div>
      </td>
    </tr>"""


# ── Consulta de datos (sin cambios) ──────────────────────────────────────────

def obtener_datos_pleno(pleno_id: str) -> dict | None:
    from db import get_client
    client = get_client()

    r = client.table("plenos").select(
        "id, fecha, tipo_sesion, resumen_ia, n_puntos, n_asistentes, n_ausentes, numero_acta"
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
     .limit(5).execute()

    r_vpleno = client.from_("v_plenos").select(
        "total_puntos, aprobados, rechazados"
    ).eq("id", pleno_id).single().execute()

    n_resolutivos = r_vpleno.data.get("total_puntos") or 0
    aprobados     = r_vpleno.data.get("aprobados") or 0
    rechazados    = r_vpleno.data.get("rechazados") or 0

    # Composición del pleno: escaños por partido (máximo de votos en cualquier punto)
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
        "composicion": composicion,
    }


# ── Generador HTML principal ─────────────────────────────────────────────────

def generar_html(datos: dict, ciudad: str = "San Sebastián") -> str:
    pleno       = datos["pleno"]
    puntos      = datos["puntos"]
    aprobados   = datos["aprobados"]
    rechazados  = datos["rechazados"]
    composicion = datos.get("composicion", [])
    n_puntos    = datos.get("n_resolutivos") or pleno.get("n_puntos", 0)
    numero      = pleno.get("numero_acta") or "—"

    fecha_fmt = _fecha_larga(pleno.get("fecha", ""))
    tipo      = (pleno.get("tipo_sesion", "ordinaria") or "ordinaria").capitalize()
    resumen   = pleno.get("resumen_ia") or ""

    # Titular: primera frase del resumen si existe, si no genérico
    titular = (resumen.split(".")[0] + ".").strip() if resumen else f"Pleno {tipo.lower()} del {fecha_fmt}"

    pleno_id   = pleno["id"]
    url_pleno  = f"{WEB_BASE_URL}/acta/{pleno_id}"

    resumen_html = _formatear_resumen(resumen) if resumen else ""
    puntos_html  = "".join(_html_punto(p) for p in puntos)
    n_extras     = max(n_puntos - len(puntos), 0)

    ver_mas_html = ""
    if n_extras > 0:
        ver_mas_html = f"""
    <tr>
      <td style="padding:20px 36px 0;">
        <a href="{url_pleno}" style="font-family:{FONT_SANS};font-size:13px;font-weight:600;color:{COLOR_ACCENT};text-decoration:none;">Ver los {n_extras} puntos restantes →</a>
      </td>
    </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Pleno {tipo} — {fecha_fmt}</title>
  <!--[if !mso]><!-->
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <!--<![endif]-->
</head>
<body style="margin:0;padding:0;background:{COLOR_BG};font-family:{FONT_SANS};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{COLOR_BG};padding:32px 16px;">
<tr><td align="center">

<!--[if mso]>
<table role="presentation" width="620" align="center" cellpadding="0" cellspacing="0"><tr><td>
<![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" width="100%" style="max-width:620px;margin:0 auto;background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:8px;">
  {_html_header(numero, ciudad)}
  {_html_masthead(tipo, fecha_fmt)}
  {_html_stats(n_puntos, aprobados, rechazados)}
  {_html_composicion(composicion)}
  {_html_asistencia(pleno)}
  {_html_resumen(resumen_html)}
  <tr>
    <td style="padding:36px 36px 8px;">
      <p style="margin:0;font-family:{FONT_SANS};font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{COLOR_INK_SOFT};">Decisiones con impacto ciudadano</p>
    </td>
  </tr>
  {puntos_html if puntos_html else f'<tr><td style="padding:16px 36px;font-family:{FONT_SANS};font-size:14px;color:{COLOR_INK_SOFT};">No hay puntos destacados en este pleno.</td></tr>'}
  <tr><td style="padding:0 36px;"><div style="border-top:1px solid {COLOR_RULE};line-height:0;font-size:0;">&nbsp;</div></td></tr>
  {ver_mas_html}
  {_html_cta(url_pleno, ciudad)}
  {_html_footer(ciudad)}
</table>
<!--[if mso]></td></tr></table><![endif]-->

</td></tr>
</table>
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
    tipo      = (datos["pleno"].get("tipo_sesion", "ordinaria") or "ordinaria").capitalize()
    asunto    = f"Pleno {tipo} de San Sebastián — {fecha_fmt}"
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
