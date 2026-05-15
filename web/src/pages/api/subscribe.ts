import type { APIRoute } from "astro";
import { createClient } from "@supabase/supabase-js";

const BREVO_HEADERS = (apiKey: string) => ({
  "api-key": apiKey,
  "Content-Type": "application/json",
});

const WEB_BASE_URL = import.meta.env.WEB_BASE_URL ?? "https://actacivium.netlify.app";

const LOGO_B64 = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAEL0lEQVR4nO1aTWzTVhx/z3GaBAO1mwah7pCtqjTEqqbbBBJCxJFA205xBdphl2RSe26lHXYcKpcdEJdddqSpNGlIfDTlhhBKihgTpzJtrNpKaJKCgH7ESZrGTux4+r/EFQIS55PODT/p6b3Y7+uf/+//8Wxj7vDHGqpAKeb/hFrOpbZURT6klUoM+p+A7nE8sdoPkL322A+c0K9jEEDKbUbhh5xLHUEmgI3hluxMHw9tCpkcmGEHfstnXg4ik4HhBtb2hAboopTFyISQc6ktqDFF0c/bMaFn1ENDPSYItnr6z4RC+fhKvNTsepiicm0VIBZb7ofa7XZb6ukfiUTl06fPiK2ua3obwO3QAM/z1jt3bvc1Os7Z73oBtZgSd1cDwWDA3sy4qclJBkpXU4huZTDLscQFC4Lf0cx4r9drRbspgOD3E5fJsmVBGoXPx9t0G4pGo8Vm5uhuCgUCxsYbDs9LUAuCv2rfsTHB1rUawM3EAfeHbiJ47PGyq1a/mZnQ9vj4RJb0jS33V4vSoiiWnE4XyS7fiQZ8PN8DxahfdGGhoLdDodl8tX4sy1JgyFAa3Ut3UihWZ+IGqYKeJhilG+GKsZ89ey7dUS8EabPRxufnb0qv5zjgZeLxuFptLM97CSVZjm0oNzI9hahGB0xNThqmDTfm5iQor1+fC4ffuPaqIUMJBgKOjgqgh/9aALq8LTCF5+Zlo7H+SnrSNRTC9XohYUwgRnb92lWulaPixsbaIaME0NnAQYduNPM0Qmi2esCq3N+GutZBZqpyb3r6Ajm4t6wBSB30tEEURS0aXSBcjkQiJNLGEwl1cXFRgXY6nS7V+ufATZI53W6a7S1rweMZoX0+H9Ewz3ttMAe0BweH1o321h024Bn17PxbD/94WGzlEF4Pgt8GCV0jkUjR6NlRW55KHGX66TPsEFn0p6e/G/IWcJI9ab0n3mvqDLCnKES3Y5KDFiueGji2H9pfuz53PMisEyN/lF9XMqpKKICxFX3CDFtHmE/Jmqe4L2yfPThOzgAJKVHaVQFW5YyqoXKQ/aCn13LONbKPCIN7EYV7yXVM2iwpgLj0r9rKxnW8pxBgVc6VMkqWvL96Vswqz+SECu0vncftumYwkpGmSUhD5Xzu1xdXaga8d0ohwPdP7hLfupQXlVV5i1Djh+K2OnH4KxJViSBYRheTP5Pn+pcSl+vyVkZ4TyEdt8XVnQO8jkxxS9MplJSfqt89/jF9P/1Xy77/VVD6m45OIClvqJoG3JfR+ZVfMu3e/N6gkIW2vVQK+Y86Mfkt8R85WXhOPNLfuSTJVtv55h5BbWO4/UqhLR7tDWQVSfvm0ewmtA9a7KDtlgOXDv2zA9NTCJe/lUhVvpXYNMm3En1LdobjdwTQbxSk7H2o4eV3p+yiUeCKlwRbBbpDm7Y6hvX7pqfQfwt5rt9zZcUNAAAAAElFTkSuQmCC";

function htmlBienvenida(nombreCiudad: string): string {
  const logoHtml = `<img src="data:image/png;base64,${LOGO_B64}" width="48" height="48" alt="Acta Civium" style="display:block;margin:0 auto;border-radius:8px;">`;

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Bienvenida a Acta Civium</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:620px;margin:32px auto 48px;">

  <!-- Cabecera -->
  <div style="background:#111827;border-radius:8px 8px 0 0;padding:36px 32px;text-align:center;">
    ${logoHtml}
    <h1 style="margin:14px 0 4px;font-family:Georgia,'Times New Roman',serif;font-size:28px;font-weight:700;color:#ffffff;letter-spacing:-.01em;">
      Acta Civium
    </h1>
    <p style="margin:0;font-size:13px;color:#9ca3af;letter-spacing:.02em;">
      El pleno municipal, explicado
    </p>
  </div>

  <!-- Subheader -->
  <div style="background:#1f2937;padding:12px 32px;text-align:center;border-bottom:1px solid #374151;">
    <p style="margin:0;font-size:13px;color:#d1d5db;">
      <span style="color:#6ee7b7;font-weight:600;text-transform:uppercase;letter-spacing:.08em;font-size:11px;">${nombreCiudad}</span>
      &nbsp;·&nbsp; Bienvenida
    </p>
  </div>

  <!-- Cuerpo -->
  <div style="background:#ffffff;padding:32px;border-radius:0 0 8px 8px;border:1px solid #e5e7eb;border-top:none;">

    <p style="margin:0 0 20px;font-family:Georgia,'Times New Roman',serif;font-size:22px;font-weight:700;color:#111827;line-height:1.3;">
      Ya formas parte de Acta Civium
    </p>

    <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.75;">
      Gracias por suscribirte. A partir de ahora recibirás un resumen cada vez que haya un pleno municipal nuevo en <strong>${nombreCiudad}</strong>.
    </p>

    <!-- Cómo funciona -->
    <div style="border-left:3px solid #2d6a4f;padding-left:16px;margin:24px 0 28px;">
      <p style="margin:0 0 12px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#2d6a4f;">Cómo funciona</p>
      <p style="margin:0 0 12px;font-size:15px;color:#374151;line-height:1.75;">
        Cuando el ayuntamiento celebra un pleno y publica el acta oficial, nuestro sistema la procesa automáticamente y elabora un resumen.
      </p>
      <p style="margin:0;font-size:15px;color:#374151;line-height:1.75;">
        Recibirás un email con las decisiones más relevantes: vivienda, urbanismo, servicios sociales, medio ambiente. Sin burocracia, en lenguaje ciudadano.
      </p>
    </div>

    <!-- Qué incluye cada número -->
    <p style="margin:0 0 14px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#2d6a4f;">Qué incluye cada newsletter</p>

    <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:28px;">
      ${[
        ["Resumen ejecutivo", "Las 3–5 decisiones más importantes del pleno."],
        ["Votaciones clave", "Quién votó qué y por qué importa."],
        ["Enfoque social y ambiental", "Impacto en vivienda, servicios sociales y derechos."],
        ["Fuente accesible", "Enlace al acta oficial para profundizar."],
      ].map(([titulo, desc]) => `
      <tr>
        <td style="padding:10px 0;border-top:1px solid #f3f4f6;vertical-align:top;width:16px;">
          <span style="font-family:Georgia,serif;font-size:18px;font-weight:700;color:#2d6a4f;line-height:1;">·</span>
        </td>
        <td style="padding:10px 0 10px 12px;border-top:1px solid #f3f4f6;">
          <p style="margin:0 0 2px;font-size:14px;font-weight:600;color:#111827;">${titulo}</p>
          <p style="margin:0;font-size:13px;color:#6b7280;">${desc}</p>
        </td>
      </tr>`).join("")}
    </table>

    <!-- Frecuencia -->
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:16px 20px;margin-bottom:28px;">
      <p style="margin:0;font-size:14px;color:#374151;line-height:1.65;">
        <strong>Frecuencia:</strong> solo cuando hay pleno nuevo (aproximadamente cada 3–6 semanas). No recibirás spam ni comunicaciones innecesarias.
      </p>
    </div>

    <!-- CTA -->
    <div style="text-align:center;margin-bottom:8px;">
      <a href="${WEB_BASE_URL}"
         style="display:inline-block;padding:13px 32px;background:#111827;color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;border-radius:6px;letter-spacing:.02em;">
        Ver las últimas actas &rarr;
      </a>
    </div>

  </div>

  <!-- Footer -->
  <div style="padding:20px 32px;text-align:center;">
    <p style="margin:0 0 6px;font-size:12px;color:#9ca3af;">
      <a href="${WEB_BASE_URL}" style="color:#6b7280;text-decoration:none;">actacivium.netlify.app</a>
      &nbsp;&middot;&nbsp; Datos públicos del Ayuntamiento de ${nombreCiudad}
    </p>
    <p style="margin:0;font-size:11px;color:#9ca3af;">
      Puedes darte de baja en cualquier momento haciendo clic aquí:
      <a href="{{ unsubscribe }}" style="color:#6b7280;text-decoration:underline;">Darme de baja</a>
    </p>
  </div>

</div>
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
