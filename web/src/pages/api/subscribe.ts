import type { APIRoute } from "astro";
import { createClient } from "@supabase/supabase-js";

const BREVO_HEADERS = (apiKey: string) => ({
  "api-key": apiKey,
  "Content-Type": "application/json",
});

const WEB_BASE_URL = import.meta.env.WEB_BASE_URL ?? "https://actacivium.netlify.app";

/* ────────────────────────────────────────────────────────────────────────────
 * Email de bienvenida v2 — alineado con el sistema visual de actacivium
 * Tipos:    Playfair Display (serif, fallback Georgia)
 *           DM Sans (body, fallback Helvetica/Arial)
 * Color:    header oscuro #1a1d1b · crema #fafaf6 · acento bosque #1f6a47
 * Estructura por <table>, estilos inline, MSO conditional wrap incluido.
 * ──────────────────────────────────────────────────────────────────────── */
function htmlBienvenida(nombreCiudad: string): string {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Bienvenida a Acta Civium</title>
  <!--[if !mso]><!-->
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
  <!--<![endif]-->
</head>
<body style="margin:0;padding:0;background:#e8eae4;font-family:'DM Sans',Helvetica,Arial,sans-serif;">

<!--[if mso]><table role="presentation" width="620" align="center" cellpadding="0" cellspacing="0"><tr><td><![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" width="100%" style="max-width:620px;margin:0 auto;border-radius:8px;overflow:hidden;border:1px solid #d0d4cc;">

  <!-- HEADER: dark band -->
  <tr>
    <td style="background:#1a1d1b;padding:22px 36px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <table role="presentation" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding-right:10px;vertical-align:middle;">
                  <img src="https://actacivium.netlify.app/favicon.svg" width="22" height="22" alt="" style="display:block;border:0;" />
                </td>
                <td style="font-family:'Playfair Display',Georgia,serif;font-size:17px;font-weight:700;letter-spacing:-0.02em;color:#ffffff;vertical-align:middle;line-height:1;">
                  Acta Civium
                </td>
              </tr>
            </table>
          </td>
          <td align="right" style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:10px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#5a6660;vertical-align:middle;">
            Núm. 0 · Bienvenida
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- HERO -->
  <tr>
    <td style="background:#fafaf6;padding:48px 36px 40px;">
      <p style="margin:0 0 14px;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:10.5px;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;color:#1f6a47;">
        ● &nbsp;${nombreCiudad}
      </p>
      <h1 style="margin:0 0 20px;font-family:'Playfair Display',Georgia,serif;font-size:40px;font-weight:700;line-height:1.05;letter-spacing:-0.03em;color:#1a1d1b;">
        El pleno municipal,<br>
        <em style="font-style:italic;color:#1f6a47;">explicado.</em>
      </h1>
      <p style="margin:0 0 32px;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:16px;line-height:1.65;color:#52555c;max-width:460px;">
        Gracias por suscribirte. Recibirás un resumen cada vez que el Ayuntamiento de <strong style="color:#1a1d1b;font-weight:600;">${nombreCiudad}</strong> celebre un pleno y publique su acta oficial.
      </p>
      <a href="${WEB_BASE_URL}" style="display:inline-block;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;color:#fff;background:#1a1d1b;text-decoration:none;padding:14px 26px;border-radius:6px;letter-spacing:0.01em;">
        Explorar las últimas actas →
      </a>
    </td>
  </tr>

  <!-- DIVIDER -->
  <tr><td style="background:#fafaf6;padding:0 36px;"><div style="border-top:1px solid #e3e5df;line-height:0;font-size:0;">&nbsp;</div></td></tr>

  <!-- CÓMO FUNCIONA -->
  <tr>
    <td style="background:#fafaf6;padding:36px 36px 32px;">
      <p style="margin:0 0 28px;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:10.5px;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;color:#9a9e9a;">
        Cómo funciona
      </p>
      ${[
        ["1", "El ayuntamiento celebra pleno",  "Aproximadamente cada 3–6 semanas. El acta oficial se publica en el portal municipal."],
        ["2", "Nuestro sistema la procesa",      "Extraemos los puntos, las votaciones por grupo y un resumen en lenguaje ciudadano."],
        ["3", "Tú recibes el resumen",           "Las decisiones que afectan a tu ciudad, sin tener que leer 90 páginas de acta."],
      ].map(([num, titulo, desc], i, arr) => `
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"${i < arr.length - 1 ? ' style="margin-bottom:20px;"' : ''}>
        <tr>
          <td width="44" valign="top">
            <div style="width:36px;height:36px;background:#e8f2ec;border-radius:50%;text-align:center;line-height:36px;font-family:'Playfair Display',Georgia,serif;font-size:15px;font-weight:700;font-style:italic;color:#1f6a47;">${num}</div>
          </td>
          <td valign="top" style="padding-top:6px;">
            <p style="margin:0 0 4px;font-family:'Playfair Display',Georgia,serif;font-size:16px;font-weight:600;color:#1a1d1b;letter-spacing:-0.01em;line-height:1.3;">${titulo}</p>
            <p style="margin:0;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:13.5px;line-height:1.6;color:#6b6f74;">${desc}</p>
          </td>
        </tr>
      </table>`).join("")}
    </td>
  </tr>

  <!-- QUÉ ENCONTRARÁS: dark section -->
  <tr>
    <td style="background:#1a1d1b;padding:36px 36px 32px;">
      <p style="margin:0 0 24px;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:10.5px;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;color:#4a5450;">
        Qué encontrarás dentro
      </p>
      ${[
        ["Resumen", "Las <strong style=\"font-weight:600;color:#eaecde;\">3–5 decisiones más importantes</strong> de cada pleno.", true,  false],
        ["Votos",   "<strong style=\"font-weight:600;color:#eaecde;\">Quién votó qué</strong> y por qué importa.",                  false, false],
        ["Impacto", "<strong style=\"font-weight:600;color:#eaecde;\">Vivienda, urbanismo, movilidad,</strong> servicios sociales, derechos…", false, false],
        ["Fuente",  "<strong style=\"font-weight:600;color:#eaecde;\">Enlace al acta oficial</strong> para profundizar.",            false, true ],
      ].map(([tag, html, first, last]) => `
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:4px;">
        <tr>
          <td style="padding:14px 16px;background:#242826;border-radius:${first ? '6px 6px 0 0' : last ? '0 0 6px 6px' : '0'};${!last ? 'border-bottom:1px solid #2e3330;' : ''}">
            <table role="presentation" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding-right:14px;vertical-align:middle;">
                  <span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#4caf80;background:#1f3329;padding:3px 8px;border-radius:3px;white-space:nowrap;">${tag}</span>
                </td>
                <td style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:13.5px;color:#c8ccc6;line-height:1.5;vertical-align:middle;">${html}</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>`).join("")}

      <!-- Honesty note -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px;">
        <tr>
          <td style="padding:14px 16px;border-left:3px solid #1f6a47;">
            <p style="margin:0;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:13px;line-height:1.65;color:#7a8a7a;">
              <strong style="color:#4caf80;font-weight:600;">Frecuencia honesta:</strong>
              solo cuando hay pleno nuevo. Sin spam, sin patrocinadores, sin trampas.
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#f2f3ef;padding:28px 36px 24px;border-top:1px solid #d8dbd4;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-family:'Playfair Display',Georgia,serif;font-size:13px;font-weight:700;letter-spacing:-0.02em;color:#1a1d1b;">
            Acta Civium
          </td>
          <td align="right" style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11px;color:#9a9e9a;">
            actacivium.netlify.app
          </td>
        </tr>
      </table>
      <p style="margin:12px 0 0;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11.5px;line-height:1.6;color:#9a9e9a;">
        Datos públicos del Ayuntamiento de ${nombreCiudad}, procesados de forma independiente.
        &nbsp;·&nbsp;
        <a href="{{ unsubscribe }}" style="color:#9a9e9a;text-decoration:underline;">Darme de baja</a>
      </p>
    </td>
  </tr>

</table>
<!--[if mso]></td></tr></table><![endif]-->

</body>
</html>`;
}

export const POST: APIRoute = async ({ request }) => {
  const { email, ciudad } = await request.json();

  if (!email || !ciudad) {
    return new Response(JSON.stringify({ error: "Faltan campos obligatorios" }), { status: 400 });
  }

  const supabase = createClient(
    import.meta.env.PUBLIC_SUPABASE_URL,
    import.meta.env.PUBLIC_SUPABASE_ANON_KEY
  );

  const { data: municipio } = await supabase
    .from("municipios")
    .select("nombre, nombre_alt, brevo_list_id")
    .eq("slug", ciudad)
    .single();

  if (!municipio?.brevo_list_id) {
    return new Response(JSON.stringify({ error: "Ciudad no configurada" }), { status: 400 });
  }

  const apiKey = import.meta.env.BREVO_API_KEY;
  if (!apiKey) {
    console.error("[subscribe] BREVO_API_KEY no está configurada en el entorno");
    return new Response(JSON.stringify({ error: "Configuración del servidor incompleta (API key)" }), { status: 500 });
  }

  const nombreCiudad = municipio.nombre_alt ?? municipio.nombre;

  const res = await fetch("https://api.brevo.com/v3/contacts", {
    method: "POST",
    headers: BREVO_HEADERS(apiKey),
    body: JSON.stringify({
      email,
      attributes: { MUNICIPIO: nombreCiudad },
      listIds: [municipio.brevo_list_id],
      updateEnabled: true,
    }),
  });

  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({}));
    return new Response(JSON.stringify({ error: err.message ?? "Error al suscribir" }), { status: 500 });
  }

  // Enviar email de bienvenida transaccional
  const senderEmail = import.meta.env.BREVO_SENDER_EMAIL;
  const senderName = import.meta.env.BREVO_SENDER_NAME ?? "Acta Civium";
  if (senderEmail) {
    const emailRes = await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: BREVO_HEADERS(apiKey),
      body: JSON.stringify({
        sender: { name: senderName, email: senderEmail },
        to: [{ email }],
        subject: `Bienvenida a Acta Civium — ${nombreCiudad}`,
        htmlContent: htmlBienvenida(nombreCiudad),
      }),
    }).catch((err) => { console.error("[bienvenida] fetch error:", err); return null; });
    if (emailRes && !emailRes.ok) {
      const errBody = await emailRes.json().catch(() => ({}));
      console.error("[bienvenida] Brevo error:", emailRes.status, JSON.stringify(errBody));
    }
  } else {
    console.warn("[bienvenida] BREVO_SENDER_EMAIL no configurado, email de bienvenida no enviado");
  }

  return new Response(JSON.stringify({ ok: true }), { status: 200 });
};
