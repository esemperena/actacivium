import type { APIRoute } from "astro";
import { createClient } from "@supabase/supabase-js";

const BREVO_HEADERS = (apiKey: string) => ({
  "api-key": apiKey,
  "Content-Type": "application/json",
});

const WEB_BASE_URL = import.meta.env.WEB_BASE_URL ?? "https://actacivium.netlify.app";

/* ────────────────────────────────────────────────────────────────────────────
 * Email de bienvenida — alineado con el sistema visual de actacivium.netlify.app
 * Tipos:    Playfair Display (serif, con fallback Georgia)
 *           DM Sans (body, con fallback Helvetica/Arial)
 * Color:    fondo crema #f4f5f0 · acento bosque #1f6a47 · tinta #1c1f24
 * Estructura por <table>, estilos inline, sin background-image, sin SVG.
 * Probado en Gmail (web + iOS), Apple Mail, Outlook (mso safe), Yahoo.
 * ──────────────────────────────────────────────────────────────────────── */
function htmlBienvenida(nombreCiudad: string): string {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Bienvenida a Acta Civium</title>
  <!--[if !mso]><!-->
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <!--<![endif]-->
</head>
<body style="margin:0;padding:0;background:#ebece8;font-family:'DM Sans',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ebece8;padding:32px 16px;">
<tr><td align="center">

<!--[if mso]>
<table role="presentation" width="620" align="center" cellpadding="0" cellspacing="0"><tr><td>
<![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" width="100%" style="max-width:620px;margin:0 auto;background:#fafaf6;border:1px solid #dde0db;border-radius:8px;">

  <!-- HEADER -->
  <tr>
    <td style="padding:36px 36px 22px;border-bottom:1px solid #e3e5df;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-family:'Playfair Display',Georgia,serif;font-size:19px;font-weight:700;letter-spacing:-0.02em;color:#1c1f24;line-height:1;">Acta Civium</td>
          <td align="right" style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:10.5px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#7a8a7d;">Núm. 0 · Bienvenida</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- HERO -->
  <tr>
    <td style="padding:48px 36px 36px;">
      <p style="margin:0 0 18px;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#1f6a47;">
        <span style="display:inline-block;width:5px;height:5px;background:#1f6a47;border-radius:50%;vertical-align:middle;margin-right:8px;opacity:.6;"></span>Bienvenida · ${nombreCiudad}
      </p>
      <h1 style="margin:0 0 18px;font-family:'Playfair Display',Georgia,serif;font-size:34px;font-weight:700;line-height:1.08;letter-spacing:-0.025em;color:#1c1f24;">
        El pleno municipal,<br>
        <em style="font-style:italic;color:#1f6a47;font-weight:600;">explicado.</em>
      </h1>
      <p style="margin:0;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:15.5px;line-height:1.65;color:#52555c;max-width:480px;">
        Gracias por suscribirte. A partir de ahora recibirás un resumen cada vez que el Ayuntamiento de
        <strong style="color:#1c1f24;font-weight:600;">${nombreCiudad}</strong> celebre un pleno y publique su acta oficial.
      </p>
    </td>
  </tr>

  <tr><td style="padding:0 36px;"><div style="border-top:1px solid #e3e5df;line-height:0;font-size:0;">&nbsp;</div></td></tr>

  <!-- CÓMO FUNCIONA -->
  <tr>
    <td style="padding:32px 36px 8px;">
      <p style="margin:0 0 22px;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#8b8e94;">Cómo funciona</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        ${[
          ["01", "El ayuntamiento celebra pleno", "Aproximadamente cada 3–6 semanas. El acta oficial se publica en donostia.eus."],
          ["02", "Nuestro sistema la procesa",    "Extraemos los puntos, las votaciones por grupo y un resumen en lenguaje ciudadano."],
          ["03", "Tú recibes el resumen",         "Las decisiones que afectan a tu ciudad, sin tener que leer 90 páginas de acta."],
        ].map(([num, titulo, desc]) => `
        <tr>
          <td width="36" valign="top" style="padding:0 12px 22px 0;">
            <span style="display:inline-block;font-family:'Playfair Display',Georgia,serif;font-size:22px;font-weight:600;font-style:italic;color:#1f6a47;line-height:1;">${num}</span>
          </td>
          <td valign="top" style="padding:0 0 22px;">
            <p style="margin:0 0 4px;font-family:'Playfair Display',Georgia,serif;font-size:16px;font-weight:600;color:#1c1f24;letter-spacing:-0.01em;line-height:1.3;">${titulo}</p>
            <p style="margin:0;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:14px;line-height:1.6;color:#52555c;">${desc}</p>
          </td>
        </tr>`).join("")}
      </table>
    </td>
  </tr>

  <tr><td style="padding:24px 36px 0;"><div style="border-top:1px solid #e3e5df;line-height:0;font-size:0;">&nbsp;</div></td></tr>

  <!-- QUÉ INCLUYE -->
  <tr>
    <td style="padding:32px 36px 16px;">
      <p style="margin:0 0 18px;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#8b8e94;">Qué encontrarás dentro</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e3e5df;border-radius:6px;">
        ${[
          ["Resumen", "Las <strong style=\"font-weight:600;\">3–5 decisiones más importantes</strong> de cada pleno."],
          ["Votos",   "<strong style=\"font-weight:600;\">Quién votó qué</strong> y por qué importa."],
          ["Impacto", "<strong style=\"font-weight:600;\">Vivienda, urbanismo, movilidad,</strong> servicios sociales, derechos…"],
          ["Fuente",  "<strong style=\"font-weight:600;\">Enlace al acta oficial</strong> para profundizar."],
        ].map(([tag, html], i, arr) => `
        <tr>
          <td style="padding:16px 18px;${i < arr.length - 1 ? 'border-bottom:1px solid #eceee9;' : ''}">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="78" valign="middle" style="padding-right:14px;">
                  <span style="display:inline-block;font-size:9.5px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#1f6a47;background:#e9f1ea;padding:3px 8px;border-radius:3px;">${tag}</span>
                </td>
                <td valign="middle" style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:14px;color:#1c1f24;line-height:1.5;">${html}</td>
              </tr>
            </table>
          </td>
        </tr>`).join("")}
      </table>
    </td>
  </tr>

  <!-- FRECUENCIA -->
  <tr>
    <td style="padding:16px 36px 0;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:16px 20px;background:#f3f7f4;border-left:3px solid #1f6a47;border-radius:0 6px 6px 0;">
            <p style="margin:0;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:13.5px;line-height:1.65;color:#3a4f43;">
              <strong style="color:#1f6a47;font-weight:600;">Frecuencia honesta:</strong>
              solo cuando hay pleno nuevo. Sin spam, sin "contenido patrocinado", sin trampas.
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- CTA -->
  <tr>
    <td align="center" style="padding:36px 36px 8px;">
      <a href="${WEB_BASE_URL}" style="display:inline-block;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;color:#ffffff;background:#1f6a47;text-decoration:none;padding:13px 28px;border-radius:6px;letter-spacing:0.01em;">
        Explorar las últimas actas →
      </a>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="padding:40px 36px 32px;">
      <div style="border-top:1px solid #e3e5df;padding-top:22px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="font-family:'Playfair Display',Georgia,serif;font-size:14px;font-weight:700;letter-spacing:-0.02em;color:#1c1f24;">Acta Civium</td>
            <td align="right" style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11px;color:#8b8e94;">actacivium.netlify.app</td>
          </tr>
        </table>
        <p style="margin:14px 0 0;font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11.5px;line-height:1.6;color:#8b8e94;">
          Datos públicos del Ayuntamiento de ${nombreCiudad}, procesados de forma independiente.
          ·
          <a href="{{ unsubscribe }}" style="color:#8b8e94;text-decoration:underline;">Darme de baja</a>
        </p>
      </div>
    </td>
  </tr>

</table>
<!--[if mso]></td></tr></table><![endif]-->

</td></tr>
</table>
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
