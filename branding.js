/**
 * ╔══════════════════════════════════════════════════════════╗
 * ║   BRANDING MÉDICO — Dr. Lorenzo Ernesto Otaño Santiago  ║
 * ║   Sistema de Gestión de Consultorio Pediátrico          ║
 * ║   Archivo central de identidad visual                   ║
 * ╚══════════════════════════════════════════════════════════╝
 *
 * Incluir en todos los módulos:
 *   <script src="branding.js"></script>
 *
 * Archivos PNG requeridos (colocar en la carpeta raíz del proyecto):
 *   logo.png             → Logo oficial del consultorio
 *   mi firma y sello.png → Firma y sello del Dr. Otaño S.
 */

// ── DATOS DEL MÉDICO ────────────────────────────────────────
const MEDICO = {
  nombre:        'Dr. Lorenzo Ernesto Otaño Santiago',
  nombreCorto:   'Dr. Lorenzo E. Otaño S.',
  iniciales:     'L.E.O.S.',
  especialidad:  'Cirujano Pediátrico · Neonatólogo · Laparoscopista',
  whatsapp:      '829-383-4449',
  email:         'ernesto1504@hotmail.com',
  exequatur:     '573-05',
  colegiatura:   '19077',
  lema:          'Cuidando con precisión la salud de tu hijo.',
  ciudad:        'Santo Domingo, República Dominicana',
};

// ── PALETA DE COLORES INSTITUCIONAL ────────────────────────
const BRAND_COLORS = {
  primary:   '#1B5FA8',
  secondary: '#2E9DD4',
  accent:    '#E07B30',
  dark:      '#1A2A4A',
  light:     '#EBF4FB',
  white:     '#FFFFFF',
  gray:      '#6B7280',
};

// ══════════════════════════════════════════════════════════════
//  IMÁGENES REALES — cargadas dinámicamente desde archivos PNG
// ══════════════════════════════════════════════════════════════

/**
 * data URI del logo PNG real — cargado desde localStorage.
 * Se guarda con setup-imagenes.html (abrir una vez para configurar).
 */
let LOGO_REAL  = null;

/**
 * data URI de la firma/sello PNG real — cargado desde localStorage.
 */
let FIRMA_REAL = null;

/** Carga las imágenes desde localStorage al iniciar */
(function _cargarImagenesGuardadas() {
  try {
    const logo  = localStorage.getItem('mc_logo_png');
    const firma = localStorage.getItem('mc_firma_png');
    if (logo)  LOGO_REAL  = logo;
    if (firma) FIRMA_REAL = firma;
  } catch(e) { /* localStorage no disponible en este contexto */ }
})();

/** Actualiza el logo en los contenedores del DOM cuando está disponible */
function _refreshLogoInDOM() {
  if (!LOGO_REAL) return;
  const logoHTML = `<img src="${LOGO_REAL}" style="height:38px;width:auto;display:block;">`;
  ['#hdr-icon', '#sidebar-brand-icon', '.brand-icon'].forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      el.innerHTML = logoHTML;
      el.style.background = 'transparent';
      el.style.padding = '0';
    });
  });
}

const _brandingReady = Promise.resolve();


// ══════════════════════════════════════════════════════════════
//  SVG DE RESERVA (usados si los PNG no están disponibles)
// ══════════════════════════════════════════════════════════════

// ── LOGO SVG (fallback) ─────────────────────────────────────
const LOGO_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 560" width="80" height="86">
  <defs>
    <clipPath id="lcc"><circle cx="258" cy="252" r="228"/></clipPath>
  </defs>
  <circle cx="258" cy="252" r="228" fill="#1B3585"/>
  <path d="M258,24 A228,228 0 0,1 258,480
           C232,468 196,442 203,398 C210,354 248,328 255,292
           C263,255 275,232 270,202 C265,173 248,156 245,130
           C242,104 250,66 258,24Z"
        fill="#2E9DD4" clip-path="url(#lcc)"/>
  <path d="M222,150 C192,178 138,234 104,296
           C73,348 77,403 113,424 C145,442 184,433 218,412
           C243,397 260,370 260,342"
        fill="white"/>
  <path d="M222,150 C243,167 272,168 310,153 L260,342Z" fill="white"/>
  <circle cx="302" cy="76" r="82" fill="white"/>
  <circle cx="216" cy="308" r="54" fill="white"/>
  <path d="M196,290 C208,274 230,272 240,285"
        fill="none" stroke="#1B3585" stroke-width="4" stroke-linecap="round"/>
  <path d="M188,310 C194,303 205,300 212,305"
        fill="none" stroke="#1B3585" stroke-width="3" stroke-linecap="round"/>
  <path d="M180,342 C165,370 173,406 200,414
           C228,422 266,405 268,376 C270,347 253,328 234,325"
        fill="white"/>
  <path d="M183,344 C196,358 215,355 226,342"
        fill="none" stroke="#1B3585" stroke-width="4" stroke-linecap="round"/>
  <path d="M237,327 C252,332 264,344 266,360"
        fill="none" stroke="#1B3585" stroke-width="3" stroke-linecap="round"/>
  <path d="M300,325 C300,313 309,307 318,312 C327,307 336,313 336,325
           C336,339 318,354 315,357 C312,354 300,339 300,325Z"
        fill="#E84520"/>
  <path d="M28,498 C128,474 390,474 492,498"
        stroke="#2E9DD4" stroke-width="9.5" fill="none" stroke-linecap="round"/>
  <path d="M50,520 C148,498 374,498 470,520"
        stroke="#E07B30" stroke-width="8.5" fill="none" stroke-linecap="round"/>
</svg>`;

// ── LOGO SVG PEQUEÑO (38px, fallback) ──────────────────────
const LOGO_SVG_SMALL = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 560" width="38" height="41">
  <defs>
    <clipPath id="lccS"><circle cx="258" cy="252" r="228"/></clipPath>
  </defs>
  <circle cx="258" cy="252" r="228" fill="#1B3585"/>
  <path d="M258,24 A228,228 0 0,1 258,480
           C232,468 196,442 203,398 C210,354 248,328 255,292
           C263,255 275,232 270,202 C265,173 248,156 245,130
           C242,104 250,66 258,24Z"
        fill="#2E9DD4" clip-path="url(#lccS)"/>
  <path d="M222,150 C192,178 138,234 104,296
           C73,348 77,403 113,424 C145,442 184,433 218,412
           C243,397 260,370 260,342"
        fill="white"/>
  <path d="M222,150 C243,167 272,168 310,153 L260,342Z" fill="white"/>
  <circle cx="302" cy="76" r="82" fill="white"/>
  <circle cx="216" cy="308" r="54" fill="white"/>
  <path d="M196,290 C208,274 230,272 240,285"
        fill="none" stroke="#1B3585" stroke-width="4" stroke-linecap="round"/>
  <path d="M180,342 C165,370 173,406 200,414
           C228,422 266,405 268,376 C270,347 253,328 234,325"
        fill="white"/>
  <path d="M183,344 C196,358 215,355 226,342"
        fill="none" stroke="#1B3585" stroke-width="4" stroke-linecap="round"/>
  <path d="M300,325 C300,313 309,307 318,312 C327,307 336,313 336,325
           C336,339 318,354 315,357 C312,354 300,339 300,325Z"
        fill="#E84520"/>
  <path d="M28,498 C128,474 390,474 492,498"
        stroke="#2E9DD4" stroke-width="9.5" fill="none" stroke-linecap="round"/>
  <path d="M50,520 C148,498 374,498 470,520"
        stroke="#E07B30" stroke-width="8.5" fill="none" stroke-linecap="round"/>
</svg>`;

// ── FIRMA SVG (fallback cursivo) ────────────────────────────
const FIRMA_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 140" width="320" height="140">
  <defs>
    <filter id="ink" x="-5%" y="-5%" width="110%" height="110%">
      <feGaussianBlur stdDeviation="0.4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g filter="url(#ink)" stroke="#1A2A9A" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M18,52 C20,30 30,20 36,28 C40,34 38,50 30,58 C24,64 16,60 18,52Z" stroke-width="2.6"/>
    <circle cx="42" cy="35" r="1.8" fill="#1A2A9A" stroke="none"/>
    <path d="M44,40 C50,36 56,30 60,22" stroke-width="2.2"/>
    <path d="M60,22 C60,22 58,55 60,72 C62,78 76,80 80,78" stroke-width="2.8"/>
    <path d="M76,56 C80,44 90,38 96,46 C100,52 97,62 90,65 C84,67 78,62 82,56 C86,50 96,48 102,54" stroke-width="2.0"/>
    <path d="M102,54 C108,44 116,40 120,48 C122,54 120,64 114,66" stroke-width="2.0"/>
    <path d="M114,50 C118,42 126,40 130,48 C132,56 128,66 122,66" stroke-width="2.0"/>
    <path d="M132,44 L148,44 L130,66 L150,66" stroke-width="1.9"/>
    <path d="M152,50 C154,42 164,40 168,48 C170,54 168,64 162,66 C156,68 150,62 154,56 C158,50 168,50 170,56" stroke-width="2.0"/>
    <path d="M176,42 L176,68 M176,42 L192,42 M176,54 L188,54 M176,68 L192,68" stroke-width="2.2"/>
    <circle cx="196" cy="68" r="2" fill="#1A2A9A" stroke="none"/>
    <path d="M204,30 C210,14 240,12 254,24 C268,36 268,64 254,76 C238,90 206,88 198,72 C190,58 196,36 204,30Z" stroke-width="3.0"/>
    <path d="M214,46 C218,38 236,38 240,46 C244,54 236,64 228,64 C220,64 212,56 216,48 C220,40 234,42 236,50" stroke-width="1.4" opacity="0.55"/>
    <path d="M254,52 C260,40 272,38 278,48 C280,54 278,66 270,68" stroke-width="2.0"/>
    <path d="M268,32 C272,26 278,26 280,32" stroke-width="1.8"/>
    <path d="M282,50 L282,72 C284,80 292,80 296,72 C298,66 296,52 290,50" stroke-width="2.0"/>
    <path d="M304,38 C316,30 320,40 312,48 C304,54 298,56 300,64 C302,72 318,74 322,68" stroke-width="2.4"/>
    <path d="M120,90 C160,84 220,86 280,90 C290,91 298,94 302,90" stroke-width="1.6" opacity="0.7"/>
    <path d="M140,96 C180,92 230,94 270,98" stroke-width="1.0" opacity="0.4"/>
  </g>
  <text x="160" y="112" text-anchor="middle" font-family="Georgia,serif" font-size="10" fill="#1A2A9A" font-weight="700" letter-spacing="0.3">Dr. Lorenzo E. Otaño S.</text>
  <text x="160" y="124" text-anchor="middle" font-family="Georgia,serif" font-size="7.5" fill="#1A2A9A" font-style="italic" letter-spacing="0.2">Cirujano Pediátrico · Neonatólogo · Laparoscopista</text>
  <text x="160" y="136" text-anchor="middle" font-family="Georgia,serif" font-size="8" fill="#1A2A9A" letter-spacing="0.3">Exeq. 573-05 · Colegiatura: 19077</text>
</svg>`;


// ══════════════════════════════════════════════════════════════
//  FUNCIONES DE BRANDING PARA DOCUMENTOS
// ══════════════════════════════════════════════════════════════

// ── MEMBRETE HTML PARA DOCUMENTOS IMPRESOS ──────────────────
function getBrandingHeader(options = {}) {
  const { compact = false, showDate = true, pageTitle = '' } = options;
  const hoy = new Date().toLocaleDateString('es-DO', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  });

  // Logo: usar PNG real si está disponible, sino SVG de reserva
  const logoGrande = LOGO_REAL
    ? `<img src="${LOGO_REAL}" style="height:80px;width:auto;display:block;flex-shrink:0;">`
    : LOGO_SVG;

  const logoCompacto = LOGO_REAL
    ? `<img src="${LOGO_REAL}" style="height:48px;width:auto;display:block;flex-shrink:0;">`
    : LOGO_SVG.replace('width="80" height="86"', 'width="44" height="47"');

  if (compact) {
    return `
    <div style="display:flex;align-items:center;gap:16px;
                border-bottom:3px solid #1B5FA8;padding-bottom:12px;margin-bottom:18px;">
      ${logoCompacto}
      <div style="flex:1;">
        <div style="font-size:1.15rem;font-weight:800;color:#1A2A4A;letter-spacing:-.3px;">
          ${MEDICO.nombreCorto}
        </div>
        <div style="font-size:.82rem;color:#2E9DD4;font-weight:600;margin:2px 0;">
          ${MEDICO.especialidad}
        </div>
        <div style="font-size:.78rem;color:#6B7280;">
          WhatsApp: ${MEDICO.whatsapp} &nbsp;|&nbsp; ${MEDICO.email}
        </div>
      </div>
      ${showDate ? `<div style="text-align:right;font-size:.78rem;color:#6B7280;">
        <div style="font-weight:600;color:#1A2A4A;">${pageTitle}</div>
        <div>${hoy}</div>
      </div>` : ''}
    </div>`;
  }

  // Membrete completo para documentos
  return `
  <div style="display:flex;align-items:center;gap:20px;
              border-bottom:3px solid #1B5FA8;padding-bottom:16px;margin-bottom:24px;">
    ${logoGrande}
    <div style="flex:1;">
      <div style="font-size:1.45rem;font-weight:800;color:#1A2A4A;letter-spacing:-.4px;">
        ${MEDICO.nombre}.
      </div>
      <div style="font-size:.95rem;color:#2E9DD4;font-weight:600;margin:3px 0;">
        ${MEDICO.especialidad}
      </div>
      <div style="font-size:.85rem;color:#6B7280;">
        WhatsApp: ${MEDICO.whatsapp} &nbsp;&nbsp;|&nbsp;&nbsp; ${MEDICO.email}
      </div>
    </div>
    ${showDate ? `<div style="text-align:right;font-size:.8rem;color:#6B7280;
                              border-left:2px solid #EBF4FB;padding-left:16px;min-width:170px;">
      ${pageTitle ? `<div style="font-size:.9rem;font-weight:700;color:#1A2A4A;margin-bottom:4px;">${pageTitle}</div>` : ''}
      <div>${hoy}</div>
      <div style="margin-top:4px;">Exequátur: <strong>${MEDICO.exequatur}</strong></div>
      <div>Colegiatura: <strong>${MEDICO.colegiatura}</strong></div>
    </div>` : ''}
  </div>`;
}

// ── PIE DE PÁGINA CON FIRMA ─────────────────────────────────
function getBrandingFooter(options = {}) {
  const { showFirma = true, showLema = true } = options;

  // Firma: usar PNG real si está disponible, sino SVG de reserva
  const firmaHTML = FIRMA_REAL
    ? `<img src="${FIRMA_REAL}"
            style="height:100px;max-width:320px;display:block;
                   filter:drop-shadow(0 1px 2px rgba(0,0,0,.08));">`
    : FIRMA_SVG;

  return `
  <div style="margin-top:40px;padding-top:0;">
    ${showFirma ? `
    <div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
      <div style="text-align:center;">
        ${firmaHTML}
      </div>
    </div>` : ''}
    ${showLema ? `
    <div style="border-top:3px solid #E07B30;padding-top:9px;text-align:center;">
      <em style="color:#1B5FA8;font-size:.88rem;font-style:italic;font-weight:600;">
        ${MEDICO.lema}
      </em>
    </div>` : ''}
  </div>`;
}

// ── CSS DE BRANDING PARA DOCUMENTOS IMPRESOS ───────────────
function getBrandingCSS() {
  return `
    @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&display=swap');
    :root {
      --brand-primary:   #1B5FA8;
      --brand-secondary: #2E9DD4;
      --brand-accent:    #E07B30;
      --brand-dark:      #1A2A4A;
      --brand-light:     #EBF4FB;
    }
    body {
      font-family: 'Segoe UI', 'EB Garamond', Georgia, sans-serif;
      color: #1A2A4A;
      background: white;
      padding: 28px 32px;
      max-width: 820px;
      margin: 0 auto;
    }
    h1, h2 {
      color: var(--brand-primary);
      border-bottom: 2px solid var(--brand-secondary);
      padding-bottom: 6px;
      margin: 20px 0 12px;
    }
    h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: .5px; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; }
    th { background: var(--brand-primary); color: white; padding: 8px 10px; font-size: .82rem; text-align: left; }
    td { padding: 7px 10px; border-bottom: 1px solid #E5ECF6; font-size: .88rem; }
    tr:nth-child(even) td { background: var(--brand-light); }
    .highlight { background: #FFF8F3; border-left: 4px solid var(--brand-accent); padding: 10px 14px; border-radius: 6px; margin: 10px 0; }
    @media print {
      body { padding: 12px 18px; }
      .no-print { display: none !important; }
    }
  `;
}

// ── DOCUMENTO HTML COMPLETO PARA VENTANA DE IMPRESIÓN ───────
function getDocumentHTML(title, bodyContent, options = {}) {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>${title} — ${MEDICO.nombreCorto}</title>
  <style>${getBrandingCSS()}</style>
</head>
<body>
  ${getBrandingHeader({ pageTitle: title, showDate: true })}
  ${bodyContent}
  ${getBrandingFooter({ showFirma: true, showLema: true })}
  <script>
    window.onload = function() {
      setTimeout(function() { window.print(); }, 400);
    };
  </script>
</body>
</html>`;
}

// ── APLICAR BRANDING AL HEADER DE LA APP ───────────────────
function applyBrandingToHeader() {
  // Intentar logo PNG real primero; si aún no cargó, usar SVG
  const logoNode = LOGO_REAL
    ? (() => { const img = document.createElement('img'); img.src = LOGO_REAL; img.style.cssText = 'height:38px;width:auto;display:block;'; return img; })()
    : null;

  const targets = ['#hdr-icon', '#sidebar-brand-icon', '.brand-icon'];
  targets.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      if (logoNode) {
        el.innerHTML = '';
        el.appendChild(logoNode.cloneNode());
        el.querySelector('img').src = LOGO_REAL;
      } else {
        el.innerHTML = LOGO_SVG_SMALL;
      }
      el.style.background = 'transparent';
      el.style.padding = '0';
    });
  });

  // Nombre y especialidad en .brand-text
  const brandText = document.querySelector('.brand-text');
  if (brandText) {
    brandText.innerHTML = `
      <div style="font-size:.95rem;font-weight:800;letter-spacing:-.2px;">${MEDICO.nombreCorto}</div>
      <div style="font-size:.72rem;font-weight:400;opacity:.85;">${MEDICO.especialidad}</div>
    `;
  }

  // Título del navegador
  if (!document.title.includes(MEDICO.nombreCorto)) {
    document.title = document.title + ' — ' + MEDICO.nombreCorto;
  }
}

// Ejecutar en DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  applyBrandingToHeader();
  // Cuando el PNG termine de cargar, actualizar logo si ya está en el DOM
  _brandingReady.then(() => _refreshLogoInDOM());
});

// Exportar para entornos Node/bundler
if (typeof module !== 'undefined') {
  module.exports = { MEDICO, LOGO_SVG, FIRMA_SVG, getBrandingHeader, getBrandingFooter, getBrandingCSS, getDocumentHTML };
}
