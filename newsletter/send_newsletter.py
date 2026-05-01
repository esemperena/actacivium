"""
Genera y envía la newsletter de Acta Civium via Brevo.
Se ejecuta automáticamente después del scraper cuando hay plenos nuevos.

Uso:
  python send_newsletter.py --pleno-id <uuid>
  python send_newsletter.py --test <tu@email.com>
"""
import os
import argparse
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.environ["BREVO_API_KEY"]
BREVO_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "3"))
BREVO_API_BASE = "https://api.brevo.com/v3"

HEADERS = {
    "api-key": BREVO_API_KEY,
    "Content-Type": "application/json",
}


def get_datos_pleno(pleno_id: str) -> dict:
    """Obtiene datos del pleno desde Supabase para construir el email."""
    import sys
    sys.path.insert(0, str(__file__).replace("newsletter/send_newsletter.py", "scraper"))
    from db import get_client

    client = get_client()

    pleno = client.table("v_plenos").select("*").eq("id", pleno_id).single().execute().data
    puntos = (
        client.table("puntos")
        .select("*")
        .eq("pleno_id", pleno_id)
        .gte("relevancia_social", 3)
        .order("relevancia_social", desc=True)
        .limit(8)
        .execute()
        .data
    )

    return {"pleno": pleno, "puntos": puntos}


def generar_html_newsletter(datos: dict, url_base: str = "https://actacivium.vercel.app") -> str:
    pleno = datos["pleno"]
    puntos = datos["puntos"]

    fecha = datetime.fromisoformat(pleno["fecha"])
    fecha_fmt = fecha.strftime("%-d de %B de %Y").replace(
        fecha.strftime("%B"), {
            "January": "enero", "February": "febrero", "March": "marzo",
            "April": "abril", "May": "mayo", "June": "junio",
            "July": "julio", "August": "agosto", "September": "septiembre",
            "October": "octubre", "November": "noviembre", "December": "diciembre",
        }.get(fecha.strftime("%B"), fecha.strftime("%B"))
    )

    CATEGORIA_LABELS = {
        "urbanismo": "Urbanismo", "vivienda": "Vivienda", "hacienda": "Hacienda",
        "medio_ambiente": "Medio Ambiente", "servicios_sociales": "Serv. Sociales",
        "movilidad": "Movilidad", "cultura": "Cultura", "gobernanza": "Gobernanza",
        "derechos": "Derechos", "otro": "Otro",
    }
    RESULTADO_LABELS = {
        "aprobado": ("Aprobado", "#1b5e20"),
        "rechazado": ("Rechazado", "#c41a1a"),
        "enterado": ("Enterado", "#555"),
    }

    puntos_html = ""
    for p in puntos:
        cat_label = CATEGORIA_LABELS.get(p.get("categoria", "otro"), "Otro")
        resultado, color = RESULTADO_LABELS.get(p.get("resultado", ""), ("", "#555"))
        unanimidad = " · unanimidad" if p.get("unanimidad") else ""
        resumen = p.get("resumen_ia", "") or ""

        puntos_html += f"""
        <tr>
          <td style="padding: 16px 0; border-bottom: 1px solid #e5e5e5;">
            <span style="display:inline-block;background:#e8f0eb;color:#1a3a2a;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:2px 8px;border-radius:2px;">{cat_label}</span>
            <p style="margin: 8px 0 4px; font-family: Georgia, serif; font-size: 15px; font-weight: 600; line-height: 1.3; color: #111;">{p.get("titulo", "")}</p>
            {f'<p style="margin: 4px 0; font-size: 13px; color: #555; line-height: 1.5;">{resumen}</p>' if resumen else ""}
            <p style="margin: 6px 0 0; font-size: 12px; color: {color}; font-weight: 600;">{resultado}{unanimidad}</p>
          </td>
        </tr>"""

    url_pleno = f"{url_base}/acta/{pleno['id']}"

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f0;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f0;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fafaf8;border:1px solid #d4d4d4;">

        <!-- Cabecera -->
        <tr>
          <td style="background:#1a3a2a;padding:24px 32px;text-align:center;">
            <p style="margin:0;font-family:Georgia,serif;font-size:28px;font-weight:700;color:#fff;letter-spacing:-0.01em;">Acta Civium</p>
            <p style="margin:8px 0 0;font-size:12px;color:#a7c5b0;letter-spacing:0.08em;text-transform:uppercase;">Plenos municipales · San Sebastián</p>
          </td>
        </tr>

        <!-- Titular -->
        <tr>
          <td style="padding:28px 32px 20px;border-bottom:3px solid #111;">
            <p style="margin:0 0 6px;font-size:11px;color:#777;text-transform:uppercase;letter-spacing:0.1em;">Nuevo pleno</p>
            <h1 style="margin:0;font-family:Georgia,serif;font-size:26px;font-weight:700;color:#111;line-height:1.15;">{fecha_fmt}</h1>
            {f'<p style="margin:12px 0 0;font-size:14px;color:#555;line-height:1.6;border-left:3px solid #1a3a2a;padding-left:12px;">{pleno.get("resumen_ia", "")}</p>' if pleno.get("resumen_ia") else ""}
          </td>
        </tr>

        <!-- Estadísticas -->
        <tr>
          <td style="padding:16px 32px;background:#fff;border-bottom:1px solid #e5e5e5;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="text-align:center;padding:8px;">
                  <p style="margin:0;font-family:Georgia,serif;font-size:24px;font-weight:700;color:#111;">{pleno.get("total_puntos", 0)}</p>
                  <p style="margin:2px 0 0;font-size:10px;color:#777;text-transform:uppercase;letter-spacing:0.08em;">Puntos</p>
                </td>
                <td style="text-align:center;padding:8px;border-left:1px solid #e5e5e5;">
                  <p style="margin:0;font-family:Georgia,serif;font-size:24px;font-weight:700;color:#1b5e20;">{pleno.get("aprobados", 0)}</p>
                  <p style="margin:2px 0 0;font-size:10px;color:#777;text-transform:uppercase;letter-spacing:0.08em;">Aprobados</p>
                </td>
                <td style="text-align:center;padding:8px;border-left:1px solid #e5e5e5;">
                  <p style="margin:0;font-family:Georgia,serif;font-size:24px;font-weight:700;color:#c41a1a;">{pleno.get("rechazados", 0)}</p>
                  <p style="margin:2px 0 0;font-size:10px;color:#777;text-transform:uppercase;letter-spacing:0.08em;">Rechazados</p>
                </td>
                <td style="text-align:center;padding:8px;border-left:1px solid #e5e5e5;">
                  <p style="margin:0;font-family:Georgia,serif;font-size:24px;font-weight:700;color:#111;">{pleno.get("unanimes", 0)}</p>
                  <p style="margin:2px 0 0;font-size:10px;color:#777;text-transform:uppercase;letter-spacing:0.08em;">Unanimidad</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Puntos relevantes -->
        <tr>
          <td style="padding:24px 32px;">
            <p style="margin:0 0 16px;font-size:11px;color:#777;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;border-bottom:1px solid #e5e5e5;padding-bottom:8px;">Decisiones con impacto ciudadano</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              {puntos_html}
            </table>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td style="padding:0 32px 28px;text-align:center;">
            <a href="{url_pleno}" style="display:inline-block;background:#1a3a2a;color:#fff;font-size:13px;font-weight:700;padding:12px 28px;text-decoration:none;">
              Ver acta completa →
            </a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#111;padding:20px 32px;text-align:center;">
            <p style="margin:0 0 8px;font-family:Georgia,serif;font-size:14px;font-weight:700;color:#fff;">Acta Civium</p>
            <p style="margin:0;font-size:11px;color:#888;">
              Datos: <a href="https://www.donostia.eus" style="color:#888;">donostia.eus</a> ·
              <a href="{url_base}/sobre" style="color:#888;">Sobre el proyecto</a> ·
              <a href="{{{{ unsubscribe }}}}" style="color:#888;">Darse de baja</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def suscribir_email(email: str) -> bool:
    """Añade un email a la lista de Brevo."""
    res = httpx.post(
        f"{BREVO_API_BASE}/contacts",
        headers=HEADERS,
        json={
            "email": email,
            "listIds": [BREVO_LIST_ID],
            "updateEnabled": True,
        },
    )
    return res.status_code in (200, 201, 204)


def enviar_newsletter(pleno_id: str, test_email: str | None = None):
    datos = get_datos_pleno(pleno_id)
    pleno = datos["pleno"]

    fecha = datetime.fromisoformat(pleno["fecha"])
    asunto = f"Pleno {fecha.strftime('%d/%m/%Y')} · San Sebastián"

    html = generar_html_newsletter(datos)

    if test_email:
        destinatarios = [{"email": test_email}]
        print(f"[TEST] Enviando a {test_email}")
    else:
        # Enviar a toda la lista
        res = httpx.post(
            f"{BREVO_API_BASE}/emailCampaigns",
            headers=HEADERS,
            json={
                "name": asunto,
                "subject": asunto,
                "sender": {"name": "Acta Civium", "email": "newsletter@actacivium.es"},
                "type": "classic",
                "htmlContent": html,
                "recipients": {"listIds": [BREVO_LIST_ID]},
                "scheduledAt": None,
            },
        )
        if res.status_code not in (200, 201):
            print(f"[!] Error creando campaña: {res.text}")
            return

        campaign_id = res.json()["id"]
        # Enviar inmediatamente
        httpx.post(
            f"{BREVO_API_BASE}/emailCampaigns/{campaign_id}/sendNow",
            headers=HEADERS,
        )
        print(f"✓ Newsletter enviada (campaña id: {campaign_id})")
        return

    # Envío de prueba
    httpx.post(
        f"{BREVO_API_BASE}/smtp/email",
        headers=HEADERS,
        json={
            "subject": f"[TEST] {asunto}",
            "sender": {"name": "Acta Civium", "email": "newsletter@actacivium.es"},
            "to": destinatarios,
            "htmlContent": html,
        },
    )
    print(f"✓ Email de prueba enviado a {test_email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pleno-id", required=True)
    parser.add_argument("--test", metavar="EMAIL", help="Enviar solo a este email")
    args = parser.parse_args()

    enviar_newsletter(args.pleno_id, args.test)
