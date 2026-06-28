"""
═══════════════════════════════════════════════════════════════════════
GENERADOR DE DOCUMENTOS PDF — CONSULTORIO MÉDICO QUIRÚRGICO PEDIÁTRICO
═══════════════════════════════════════════════════════════════════════
Genera todos los documentos clínicos automáticamente:
  - Receta médica
  - Consentimiento informado
  - Descripción quirúrgica
  - Nota preoperatoria / postoperatoria
  - Epicrisis
  - Indicaciones postoperatorias
  - Solicitud a aseguradora
  - Certificado médico
  - Carta de referencia
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, Image, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from datetime import date, datetime
from io import BytesIO
import os

# ─── Colores del consultorio ──────────────────────────────────
NAVY   = colors.HexColor('#1B3A5C')
TEAL   = colors.HexColor('#0E7C7B')
ACCENT = colors.HexColor('#2E86AB')
LIGHT  = colors.HexColor('#EAF4F4')
GRAY   = colors.HexColor('#F5F5F5')
WHITE  = colors.white
BLACK  = colors.black
RED    = colors.HexColor('#C0392B')

# ─── Datos del médico (configurables) ─────────────────────────
MEDICO_CONFIG = {
    "nombre":          "Dr. ___________________________",
    "especialidad":    "Médico Cirujano Pediatra",
    "cedula_medica":   "CM-___________",
    "cedula_personal": "V-___________",
    "telefono":        "_______________",
    "email":           "_____@consultorio.med",
    "direccion":       "Consultorio ____, Piso ___, _______________",
    "ciudad":          "Caracas, Venezuela",
    "logo_path":       None,  # Ruta al logo del consultorio
}

def get_styles():
    """Retorna los estilos del documento"""
    styles = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("title",    fontName="Helvetica-Bold",   fontSize=16, textColor=NAVY,   alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica-Bold",   fontSize=12, textColor=TEAL,   alignment=TA_CENTER, spaceAfter=2),
        "header":   ParagraphStyle("header",   fontName="Helvetica-Bold",   fontSize=10, textColor=NAVY,   spaceAfter=4),
        "body":     ParagraphStyle("body",     fontName="Helvetica",        fontSize=10, textColor=BLACK,  spaceAfter=6, leading=14),
        "bodyJ":    ParagraphStyle("bodyJ",    fontName="Helvetica",        fontSize=10, textColor=BLACK,  spaceAfter=6, leading=14, alignment=TA_JUSTIFY),
        "small":    ParagraphStyle("small",    fontName="Helvetica",        fontSize=8,  textColor=colors.grey, spaceAfter=2),
        "bold":     ParagraphStyle("bold",     fontName="Helvetica-Bold",   fontSize=10, textColor=BLACK,  spaceAfter=4),
        "center":   ParagraphStyle("center",   fontName="Helvetica",        fontSize=10, textColor=BLACK,  alignment=TA_CENTER),
        "right":    ParagraphStyle("right",    fontName="Helvetica",        fontSize=9,  textColor=colors.grey, alignment=TA_RIGHT),
        "rx":       ParagraphStyle("rx",       fontName="Helvetica-BoldOblique", fontSize=28, textColor=TEAL, spaceAfter=8),
        "section":  ParagraphStyle("section",  fontName="Helvetica-Bold",   fontSize=11, textColor=WHITE,  backColor=TEAL, spaceAfter=0, spaceBefore=0, leftIndent=6),
    }

def make_header(styles, title: str, numero: str = "", fecha: str = "") -> list:
    """Genera el encabezado estándar del consultorio"""
    s = styles
    elements = []

    # Línea de membrete
    header_data = [[
        Paragraph(f"<b>{MEDICO_CONFIG['nombre']}</b><br/>{MEDICO_CONFIG['especialidad']}<br/>"
                  f"CM: {MEDICO_CONFIG['cedula_medica']} | Tel: {MEDICO_CONFIG['telefono']}<br/>"
                  f"{MEDICO_CONFIG['email']}", s["body"]),
        Paragraph(f"<b>{title}</b><br/>"
                  f"{'N°: ' + numero if numero else ''}<br/>"
                  f"Fecha: {fecha or date.today().strftime('%d/%m/%Y')}", s["right"]),
    ]]
    header_table = Table(header_data, colWidths=[10*cm, 7.5*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN',     (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW',  (0,0), (-1,-1), 1.5, TEAL),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*cm))
    return elements

def make_patient_box(styles, paciente: dict) -> Table:
    """Caja de datos del paciente"""
    s = styles
    nombre = paciente.get("nombre_completo", "—")
    edad   = paciente.get("edad_anios", "—")
    nac    = paciente.get("fecha_nacimiento", "")
    if isinstance(nac, date): nac = nac.strftime("%d/%m/%Y")
    exp    = paciente.get("numero_expediente", "—")
    tutor  = paciente.get("tutor_nombre", "—")
    seguro = paciente.get("aseguradora_nombre") or "Particular"
    poliza = paciente.get("numero_poliza", "—")

    data = [[
        Paragraph(f"<b>Paciente:</b> {nombre}", s["body"]),
        Paragraph(f"<b>Expediente:</b> {exp}", s["body"]),
    ],[
        Paragraph(f"<b>Edad:</b> {edad} años | <b>Nac.:</b> {nac}", s["body"]),
        Paragraph(f"<b>Tutor:</b> {tutor}", s["body"]),
    ],[
        Paragraph(f"<b>Aseguradora:</b> {seguro}", s["body"]),
        Paragraph(f"<b>Póliza:</b> {poliza}", s["body"]),
    ]]
    t = Table(data, colWidths=[8.75*cm, 8.75*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT),
        ('GRID',       (0,0), (-1,-1), 0.5, TEAL),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
    ]))
    return t

# ═══════════════════════════════════════════════════════════════
# GENERADORES DE DOCUMENTOS
# ═══════════════════════════════════════════════════════════════

def generar_receta(receta: dict, paciente: dict) -> bytes:
    """Genera receta médica profesional en PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    s = get_styles()
    elements = make_header(s, "RECETA MÉDICA", receta.get("numero_receta",""),
                           str(receta.get("fecha_emision", date.today())))
    elements.append(make_patient_box(s, paciente))
    elements.append(Spacer(1, 0.4*cm))

    # Peso para cálculo
    if receta.get("peso_usado_kg"):
        elements.append(Paragraph(f"Peso utilizado para cálculo de dosis: <b>{receta['peso_usado_kg']} kg</b>", s["small"]))

    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("℞", s["rx"]))

    # Medicamentos
    medicamentos = receta.get("medicamentos", [])
    for i, med in enumerate(medicamentos):
        med_text = (f"<b>{i+1}. {med.get('nombre','—')}</b> — {med.get('presentacion','')}<br/>"
                    f"Dosis: <b>{med.get('dosis_calculada_mg','')} mg</b> ({med.get('dosis_texto','')})"
                    f" | Frecuencia: <b>{med.get('frecuencia','')}</b>"
                    f" | Duración: <b>{med.get('duracion_dias','')} días</b>"
                    f" | Vía: {med.get('via','oral')}")
        if med.get("instrucciones"):
            med_text += f"<br/><i>{med['instrucciones']}</i>"
        box = Table([[Paragraph(med_text, s["body"])]], colWidths=[17.5*cm])
        box.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), LIGHT if i%2==0 else WHITE),
            ('LEFTBORDERPADDING', (0,0), (-1,-1), 8),
            ('BOX',           (0,0), (-1,-1), 0.5, TEAL),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ]))
        elements.append(box)
        elements.append(Spacer(1, 0.15*cm))

    if receta.get("instrucciones_generales"):
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("<b>Instrucciones generales:</b>", s["header"]))
        elements.append(Paragraph(receta["instrucciones_generales"], s["bodyJ"]))

    # Pie de firma
    elements.append(Spacer(1, 1.5*cm))
    firma_data = [["", ""],
                  [Paragraph("_______________________________", s["center"]),
                   Paragraph(f"<b>{MEDICO_CONFIG['nombre']}</b><br/>{MEDICO_CONFIG['especialidad']}<br/>{MEDICO_CONFIG['cedula_medica']}", s["center"])]]
    firma_t = Table(firma_data, colWidths=[8*cm, 9.5*cm])
    firma_t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (1,1),(1,1), 0)]))
    elements.append(firma_t)

    doc.build(elements)
    return buffer.getvalue()


def generar_descripcion_quirurgica(cirugia: dict, paciente: dict) -> bytes:
    """Genera la descripción quirúrgica completa"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    s = get_styles()
    elements = make_header(s, "DESCRIPCIÓN QUIRÚRGICA", cirugia.get("numero_cirugia",""),
                           str(cirugia.get("fecha_cirugia", date.today())))
    elements.append(make_patient_box(s, paciente))
    elements.append(Spacer(1, 0.4*cm))

    def section(title):
        t = Table([[Paragraph(f"  {title}", s["section"])]], colWidths=[17.5*cm])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), TEAL), ('BOTTOMPADDING',(0,0),(-1,-1),4), ('TOPPADDING',(0,0),(-1,-1),4)]))
        elements.append(t)
        elements.append(Spacer(1, 0.2*cm))

    section("DATOS DEL PROCEDIMIENTO")
    datos = [
        ["Procedimiento:", cirugia.get("procedimiento","—"), "CPT:", cirugia.get("codigo_cpt","—")],
        ["Tipo:", cirugia.get("tipo_cirugia","electiva"), "Estado:", cirugia.get("estado","—")],
        ["Hospital:", cirugia.get("hospital","—"), "Sala:", cirugia.get("sala_quirurgica","—")],
        ["Anestesia:", cirugia.get("tipo_anestesia","general"), "Anestesiólogo:", cirugia.get("anestesiologo","—")],
        ["Ayudante 1:", cirugia.get("ayudante_1","—"), "Ayudante 2:", cirugia.get("ayudante_2","—")],
        ["Hora inicio:", str(cirugia.get("hora_inicio","—")), "Hora fin:", str(cirugia.get("hora_fin","—"))],
    ]
    dt = Table(datos, colWidths=[3.5*cm, 5.25*cm, 3.5*cm, 5.25*cm])
    dt.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',  (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), NAVY),
        ('TEXTCOLOR', (2,0), (2,-1), NAVY),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT, WHITE]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(dt)
    elements.append(Spacer(1, 0.4*cm))

    if cirugia.get("diagnostico_quirurgico"):
        section("DIAGNÓSTICO QUIRÚRGICO")
        elements.append(Paragraph(cirugia["diagnostico_quirurgico"], s["bodyJ"]))
        elements.append(Spacer(1, 0.3*cm))

    section("DESCRIPCIÓN DEL ACTO QUIRÚRGICO")
    desc = cirugia.get("descripcion_quirurgica") or "Ver registro intraoperatorio adjunto."
    elements.append(Paragraph(desc, s["bodyJ"]))
    elements.append(Spacer(1, 0.3*cm))

    if cirugia.get("hallazgos_intraop"):
        section("HALLAZGOS INTRAOPERATORIOS")
        elements.append(Paragraph(cirugia["hallazgos_intraop"], s["bodyJ"]))
        elements.append(Spacer(1, 0.3*cm))

    if cirugia.get("complicaciones"):
        section("COMPLICACIONES")
        elements.append(Paragraph(cirugia["complicaciones"], s["bodyJ"]))
    else:
        section("COMPLICACIONES")
        elements.append(Paragraph("Sin complicaciones intraoperatorias.", s["body"]))
    elements.append(Spacer(1, 0.3*cm))

    # Materiales
    materiales = cirugia.get("materiales_utilizados", [])
    if materiales:
        section("MATERIALES E IMPLANTES UTILIZADOS")
        for mat in materiales:
            elements.append(Paragraph(f"• {mat}", s["body"]))
        elements.append(Spacer(1, 0.3*cm))

    # Firma
    elements.append(Spacer(1, 1*cm))
    firma_data = [[Paragraph("_______________________________<br/>"
                             f"<b>{MEDICO_CONFIG['nombre']}</b><br/>"
                             f"{MEDICO_CONFIG['especialidad']}<br/>"
                             f"{MEDICO_CONFIG['cedula_medica']}", s["center"])]]
    firma_t = Table(firma_data, colWidths=[17.5*cm])
    firma_t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    elements.append(firma_t)

    doc.build(elements)
    return buffer.getvalue()


def generar_consentimiento_informado(cirugia: dict, paciente: dict) -> bytes:
    """Genera el consentimiento informado para cirugía"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    s = get_styles()
    elements = make_header(s, "CONSENTIMIENTO INFORMADO")
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("CONSENTIMIENTO INFORMADO PARA PROCEDIMIENTO QUIRÚRGICO", s["title"]))
    elements.append(Spacer(1, 0.5*cm))

    tutor  = paciente.get("tutor_nombre","__________________________")
    nombre = paciente.get("nombre_completo","__________________________")
    proc   = cirugia.get("procedimiento","__________________________")
    diag   = cirugia.get("diagnostico_quirurgico","__________________________")

    texto = f"""
Yo, <b>{tutor}</b>, titular de la cédula de identidad N° ________________________,
en mi condición de representante legal del menor <b>{nombre}</b>,
fecha de nacimiento: {paciente.get('fecha_nacimiento','—')}, hago constar que:
<br/><br/>
<b>1. INFORMACIÓN RECIBIDA:</b> He sido informado(a) de manera clara y comprensible por el
{MEDICO_CONFIG['especialidad']}, sobre el diagnóstico de <b>{diag}</b> y la necesidad
de realizar el procedimiento quirúrgico denominado: <b>{proc}</b>.
<br/><br/>
<b>2. NATURALEZA DEL PROCEDIMIENTO:</b> Se me ha explicado en qué consiste la intervención,
su propósito terapéutico, los pasos del procedimiento y el tipo de anestesia que se utilizará
({cirugia.get('tipo_anestesia','general')}).
<br/><br/>
<b>3. RIESGOS Y COMPLICACIONES:</b> He sido informado(a) sobre los posibles riesgos inherentes
al procedimiento, incluyendo pero no limitándose a: sangrado, infección, reacción a la anestesia,
lesión de estructuras adyacentes, complicaciones respiratorias, y otras propias del procedimiento específico.
<br/><br/>
<b>4. BENEFICIOS ESPERADOS:</b> El médico me ha explicado los beneficios esperados del procedimiento
y las consecuencias de no realizarlo.
<br/><br/>
<b>5. ALTERNATIVAS:</b> Se me han informado las alternativas de tratamiento disponibles.
<br/><br/>
<b>6. PREGUNTAS RESPONDIDAS:</b> He tenido la oportunidad de hacer preguntas, las cuales han
sido respondidas de manera satisfactoria.
<br/><br/>
<b>7. AUTORIZACIÓN:</b> Con base en la información recibida, <b>AUTORIZO VOLUNTARIAMENTE</b>
al equipo médico encabezado por {MEDICO_CONFIG['nombre']} a realizar el procedimiento descrito
y cualquier otro que sea necesario por razones terapéuticas durante el acto quirúrgico.
"""
    elements.append(Paragraph(texto, s["bodyJ"]))
    elements.append(Spacer(1, 1*cm))

    # Firmas
    firmas_data = [
        [Paragraph("<b>REPRESENTANTE LEGAL</b>", s["center"]),
         Paragraph("<b>MÉDICO CIRUJANO</b>", s["center"])],
        [Spacer(1, 1.5*cm), Spacer(1, 1.5*cm)],
        [Paragraph("_____________________________<br/>Nombre: " + tutor + "<br/>Cédula: _______________<br/>Teléfono: _______________", s["center"]),
         Paragraph(f"_____________________________<br/>{MEDICO_CONFIG['nombre']}<br/>{MEDICO_CONFIG['cedula_medica']}<br/>Sello", s["center"])],
    ]
    firmas_t = Table(firmas_data, colWidths=[8.75*cm, 8.75*cm])
    firmas_t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(firmas_t)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Fecha y lugar: {date.today().strftime('%d/%m/%Y')} — {MEDICO_CONFIG['ciudad']}", s["center"]))

    doc.build(elements)
    return buffer.getvalue()


def generar_indicaciones_postop(cirugia: dict, paciente: dict, indicaciones_custom: str = None) -> bytes:
    """Genera las indicaciones postoperatorias"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    s = get_styles()
    elements = make_header(s, "INDICACIONES POSTOPERATORIAS")
    elements.append(make_patient_box(s, paciente))
    elements.append(Spacer(1, 0.4*cm))

    elements.append(Paragraph(f"<b>Procedimiento realizado:</b> {cirugia.get('procedimiento','—')}", s["body"]))
    elements.append(Paragraph(f"<b>Fecha de cirugía:</b> {cirugia.get('fecha_cirugia','—')}", s["body"]))
    elements.append(Spacer(1, 0.3*cm))

    if indicaciones_custom:
        elements.append(Paragraph(indicaciones_custom, s["bodyJ"]))
    else:
        indicaciones_default = [
            "Reposo relativo según tolerancia del paciente.",
            "Dieta: según indicación del médico tratante.",
            "Cuidados de la herida: mantener seca y limpia durante las primeras 48 horas.",
            "Baño normal permitido a partir de las 48-72 horas, evitando mojar directamente la herida.",
            f"Analgesia: Acetaminofén 15mg/kg/dosis cada 6 horas si dolor.",
            "Ibuprofeno 10mg/kg/dosis cada 8 horas con alimentos si persiste el dolor.",
            "Control médico en 7 días o antes si presenta alguna complicación.",
        ]
        alarmas = [
            "Fiebre mayor de 38.5°C que no cede con acetaminofén.",
            "Sangrado activo o secreción purulenta por la herida.",
            "Enrojecimiento excesivo, calor o edema importante en la zona operatoria.",
            "Dolor intenso que no cede con analgésicos indicados.",
            "Vómitos persistentes o incapacidad para hidratarse.",
            "Cualquier otro síntoma que le genere preocupación.",
        ]

        elements.append(Paragraph("INDICACIONES GENERALES:", s["header"]))
        for i, ind in enumerate(indicaciones_default):
            elements.append(Paragraph(f"{i+1}. {ind}", s["body"]))

        elements.append(Spacer(1, 0.4*cm))
        t = Table([[Paragraph("<b>⚠️ SEÑALES DE ALARMA — ACUDIR INMEDIATAMENTE A URGENCIAS SI PRESENTA:</b>", s["body"])]], colWidths=[17.5*cm])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF3CD')), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E8871A')), ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6), ('LEFTPADDING',(0,0),(-1,-1),8)]))
        elements.append(t)
        for alarma in alarmas:
            elements.append(Paragraph(f"• {alarma}", s["body"]))

    elements.append(Spacer(1, 0.4*cm))
    elements.append(Paragraph(f"<b>Contacto del médico:</b> {MEDICO_CONFIG['telefono']} — {MEDICO_CONFIG['email']}", s["body"]))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"_______________________________<br/><b>{MEDICO_CONFIG['nombre']}</b><br/>{MEDICO_CONFIG['especialidad']}<br/>{MEDICO_CONFIG['cedula_medica']}", s["center"]))

    doc.build(elements)
    return buffer.getvalue()


def generar_solicitud_aseguradora(solicitud: dict, paciente: dict, aseguradora: dict) -> bytes:
    """Genera carta de solicitud a aseguradora"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    s = get_styles()
    elements = make_header(s, "SOLICITUD DE AUTORIZACIÓN MÉDICA", solicitud.get("numero_solicitud",""))
    elements.append(Spacer(1, 0.5*cm))

    # Destinatario
    elements.append(Paragraph(f"<b>{aseguradora.get('nombre','Aseguradora')}</b><br/>"
                               f"Departamento de Autorizaciones Médicas<br/>"
                               f"Fecha: {date.today().strftime('%d de %B de %Y')}", s["body"]))
    elements.append(Spacer(1, 0.4*cm))
    elements.append(Paragraph("Estimados señores,", s["body"]))
    elements.append(Spacer(1, 0.2*cm))

    nombre = paciente.get("nombre_completo","—")
    poliza = paciente.get("numero_poliza","—")
    tipo   = solicitud.get("tipo_solicitud","quirúrgica")

    elements.append(Paragraph(
        f"Por medio de la presente, me dirijo a ustedes en mi condición de {MEDICO_CONFIG['especialidad']}, "
        f"a fin de solicitar la <b>autorización {tipo}</b> para el paciente(a) <b>{nombre}</b>, "
        f"titular de la póliza N° <b>{poliza}</b>.",
        s["bodyJ"]))
    elements.append(Spacer(1, 0.3*cm))

    # Datos clínicos
    elements.append(Paragraph("<b>INFORMACIÓN CLÍNICA:</b>", s["header"]))
    datos = [
        ["Diagnóstico (CIE-10):", f"{solicitud.get('diagnostico_cie10','—')} — {solicitud.get('diagnostico_texto','—')}"],
        ["Procedimiento solicitado:", solicitud.get("procedimiento_texto","—")],
        ["Tipo de solicitud:", tipo],
    ]
    dt = Table(datos, colWidths=[5*cm, 12.5*cm])
    dt.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT, WHITE]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(dt)
    elements.append(Spacer(1, 0.4*cm))

    elements.append(Paragraph("<b>JUSTIFICACIÓN MÉDICA:</b>", s["header"]))
    elements.append(Paragraph(solicitud.get("justificacion_medica","—"), s["bodyJ"]))
    elements.append(Spacer(1, 0.3*cm))

    elements.append(Paragraph(
        "En virtud de lo expuesto, solicito respetuosamente la pronta tramitación y autorización de lo requerido, "
        "a fin de garantizar la atención oportuna y necesaria del paciente.",
        s["bodyJ"]))
    elements.append(Spacer(1, 1*cm))

    elements.append(Paragraph(f"Atentamente,<br/><br/><br/>"
                               f"_______________________________<br/>"
                               f"<b>{MEDICO_CONFIG['nombre']}</b><br/>"
                               f"{MEDICO_CONFIG['especialidad']}<br/>"
                               f"{MEDICO_CONFIG['cedula_medica']}<br/>"
                               f"Tel: {MEDICO_CONFIG['telefono']}", s["body"]))

    doc.build(elements)
    return buffer.getvalue()


def generar_certificado_medico(paciente: dict, diagnostico: str, restricciones: str, dias_reposo: int = 0) -> bytes:
    """Genera certificado médico"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2.5*cm, rightMargin=2.5*cm)
    s = get_styles()
    elements = make_header(s, "CERTIFICADO MÉDICO")
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("CERTIFICADO MÉDICO", s["title"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=TEAL))
    elements.append(Spacer(1, 0.8*cm))

    texto = (
        f"El suscrito, <b>{MEDICO_CONFIG['nombre']}</b>, {MEDICO_CONFIG['especialidad']}, "
        f"con cédula médica {MEDICO_CONFIG['cedula_medica']}, hace constar que:"
        f"<br/><br/>"
        f"El/La paciente <b>{paciente.get('nombre_completo','—')}</b>, de <b>{paciente.get('edad_anios','—')} años</b> de edad, "
        f"con fecha de nacimiento {paciente.get('fecha_nacimiento','—')}, "
        f"acudió a consulta y fue evaluado(a) en este consultorio, encontrándosele: "
        f"<b>{diagnostico}</b>."
        f"<br/><br/>"
        f"{restricciones}"
    )

    if dias_reposo > 0:
        texto += (
            f"<br/><br/>"
            f"Por lo antes expuesto, se le indica reposo médico por <b>{dias_reposo} {'día' if dias_reposo==1 else 'días'}</b>, "
            f"a partir de la fecha de emisión del presente certificado."
        )

    elements.append(Paragraph(texto, s["bodyJ"]))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(
        f"Se expide el presente certificado a solicitud de la parte interesada, "
        f"en {MEDICO_CONFIG['ciudad']}, a los {date.today().day} días del mes de "
        f"{date.today().strftime('%B')} de {date.today().year}.",
        s["bodyJ"]))

    elements.append(Spacer(1, 1.5*cm))
    elements.append(Paragraph(
        f"_______________________________<br/>"
        f"<b>{MEDICO_CONFIG['nombre']}</b><br/>"
        f"{MEDICO_CONFIG['especialidad']}<br/>"
        f"{MEDICO_CONFIG['cedula_medica']}<br/>"
        f"Sello del consultorio", s["center"]))

    doc.build(elements)
    return buffer.getvalue()
