from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, KeepInFrame)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import os
from datetime import date

PURPLE  = colors.HexColor('#a955b3')
CYAN    = colors.HexColor('#00CCCC')
BLACK   = colors.HexColor('#111111')
DGRAY   = colors.HexColor('#555555')
GRAY    = colors.HexColor('#B3B3B3')
LGRAY   = colors.HexColor('#F5F5F5')
WHITE   = colors.white
W, H    = A4  # 595.28 x 841.89 pt

# ── Configuración editable ───────────────────────────────────────────────────
TASA_IVA   = 0.15   # Cambiar aquí cuando cambie la tasa
PCT_SCVS   = 0.035  # Superintendencia de Bancos
PCT_CAMP   = 0.005  # Seguro Campesino

def calcular_prima(prima_neta):
    scvs    = prima_neta * PCT_SCVS
    camp    = prima_neta * PCT_CAMP
    if prima_neta <= 250:    emision = 0.50
    elif prima_neta <= 500:  emision = 1.00
    elif prima_neta <= 1000: emision = 3.00
    elif prima_neta <= 2000: emision = 5.00
    elif prima_neta <= 4000: emision = 7.00
    else:                    emision = 9.00
    base  = prima_neta + scvs + camp + emision
    iva   = base * TASA_IVA
    total = base + iva
    return dict(prima_neta=prima_neta, scvs=scvs, camp=camp,
                emision=emision, base=base, iva=iva, total=total)

BADGE_COLORS = {
    'economico':    (colors.HexColor('#E8F5E9'), colors.HexColor('#2E7D32')),
    'cobertura':    (colors.HexColor('#F3E5F5'), colors.HexColor('#6A1B9A')),
    'deducible':    (colors.HexColor('#E3F2FD'), colors.HexColor('#1565C0')),
    'flexibilidad': (colors.HexColor('#FFF8E1'), colors.HexColor('#E65100')),
    'tecnologia':   (colors.HexColor('#E0F7FA'), colors.HexColor('#00695C')),
}

def E():
    return {
        'seccion':    ParagraphStyle('s',  fontName='Helvetica-Bold',    fontSize=8.5,textColor=PURPLE, leading=12, spaceBefore=3),
        'tabla_hdr':  ParagraphStyle('th', fontName='Helvetica-Bold',    fontSize=7.5,textColor=WHITE,  leading=10),
        'tabla_cel':  ParagraphStyle('tc', fontName='Helvetica',         fontSize=7.5,textColor=BLACK,  leading=10),
        'tabla_bold': ParagraphStyle('tb', fontName='Helvetica-Bold',    fontSize=7.5,textColor=BLACK,  leading=10),
        'tabla_gray': ParagraphStyle('tg', fontName='Helvetica',         fontSize=7,  textColor=DGRAY,  leading=9),
        'nota':       ParagraphStyle('n',  fontName='Helvetica-Oblique', fontSize=7,  textColor=GRAY,   leading=10),
        'prima_xl':   ParagraphStyle('px', fontName='Helvetica-Bold',    fontSize=16, textColor=PURPLE, leading=20),
        'prima_md':   ParagraphStyle('pm', fontName='Helvetica-Bold',    fontSize=9.5,textColor=DGRAY,  leading=12),
        'plan_tit':   ParagraphStyle('pt', fontName='Helvetica-Bold',    fontSize=11, textColor=BLACK,  leading=14),
        'plan_aseg':  ParagraphStyle('pa', fontName='Helvetica-Bold',    fontSize=13, textColor=PURPLE, leading=16),
        'lbl':        ParagraphStyle('l',  fontName='Helvetica',         fontSize=7.5,textColor=GRAY,   leading=11),
        'dato':       ParagraphStyle('d',  fontName='Helvetica-Bold',    fontSize=7.5,textColor=BLACK,  leading=11),
    }

# ── Canvas ────────────────────────────────────────────────────────────────────
class BrandedCanvas(canvas.Canvas):
    def __init__(self, filename, logo_path, **kwargs):
        super().__init__(filename, **kwargs)
        self.logo_path = logo_path
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._chrome()
            super().showPage()
        super().save()

    def _chrome(self):
        # Header blanco
        self.setFillColor(WHITE)
        self.rect(0, H - 55*mm, W, 55*mm, fill=1, stroke=0)
        self.setFillColor(CYAN)
        self.rect(0, H - 56.5*mm, W, 2*mm, fill=1, stroke=0)
        self.setFillColor(PURPLE)
        self.rect(0, H - 55.2*mm, W, 0.5*mm, fill=1, stroke=0)
        if os.path.exists(self.logo_path):
            self.drawImage(self.logo_path, 12*mm, H - 50*mm,
                           width=46*mm, height=40*mm,
                           preserveAspectRatio=True, mask='auto')
        self.setFont('Helvetica-Bold', 12.5)
        self.setFillColor(BLACK)
        self.drawRightString(W - 12*mm, H - 24*mm, 'Propuesta de seguro vehicular')
        self.setFont('Helvetica', 8)
        self.setFillColor(PURPLE)
        self.drawRightString(W - 12*mm, H - 33*mm, 'Seguros Soledad Sáenz  ·  Quito, Ecuador')
        # Footer negro
        self.setFillColor(BLACK)
        self.rect(0, 0, W, 16*mm, fill=1, stroke=0)
        self.setFillColor(CYAN)
        self.rect(0, 16*mm, W, 1.2*mm, fill=1, stroke=0)
        self.setFont('Helvetica', 6.5)
        self.setFillColor(GRAY)
        self.drawCentredString(W/2, 9.5*mm,
            'Seguros Soledad Sáenz  ·  Bermejo N40K y de los Motilones, Ofc. 3A, Edif. Le Bois, Quito  ·  ssasesores.com.ec')
        self.drawCentredString(W/2, 4.5*mm,
            'Documento referencial — no constituye póliza de seguro ni otorga cobertura')

def mk_badge(texto, tipo):
    bg, fg = BADGE_COLORS.get(tipo, (LGRAY, DGRAY))
    st = ParagraphStyle('b', fontName='Helvetica-Bold', fontSize=7, textColor=fg, leading=9)
    t = Table([[Paragraph(texto, st)]])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),bg),
        ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('ROUNDEDCORNERS',[4]),
    ]))
    return t

def fila_dato(label, valor, e):
    return [Paragraph(label, e['lbl']), Paragraph(str(valor), e['dato'])]

# ── Página 1: resumen ─────────────────────────────────────────────────────────
def pagina_resumen(story, datos, e, doc):
    hoy = date.today().strftime('%d/%m/%Y')
    col = doc.width / 2 - 3*mm

    story.append(Table(
        [[Paragraph('Comparativa de opciones', e['seccion']),
          Paragraph(f'Fecha: {hoy}', ParagraphStyle('f', fontName='Helvetica',
                    fontSize=7.5, textColor=GRAY, alignment=TA_RIGHT))]],
        colWidths=[doc.width*0.6, doc.width*0.4]
    ))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRAY))
    story.append(Spacer(1, 3*mm))

    tc = Table([
        fila_dato('Nombre', datos['nombre'], e),
        fila_dato('Cédula', datos['cedula'], e),
        fila_dato('Teléfono', datos.get('telefono',''), e),
        fila_dato('Correo', datos.get('correo',''), e),
    ], colWidths=[col*0.36, col*0.64])
    tc.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,LGRAY]),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),4),
    ]))
    tv = Table([
        fila_dato('Vehículo', f"{datos['marca']} {datos['modelo']}", e),
        fila_dato('Año', datos['anio'], e),
        fila_dato('Placa', datos['placa'], e),
        fila_dato('Valor asegurado', f"$ {datos['valor']:,.2f}", e),
    ], colWidths=[col*0.36, col*0.64])
    tv.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,LGRAY]),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),4),
    ]))
    blq = Table(
        [[Paragraph('Datos del cliente', e['seccion']),
          Paragraph('Datos del vehículo', e['seccion'])],
         [tc, tv]],
        colWidths=[col+3*mm, col+3*mm]
    )
    blq.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LINEAFTER',(0,0),(0,-1),0.5,GRAY),
        ('RIGHTPADDING',(0,0),(0,-1),8),('LEFTPADDING',(1,0),(1,-1),8),
    ]))
    story.append(blq)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('Opciones disponibles', e['seccion']))
    story.append(Spacer(1, 2*mm))

    planes = datos.get('planes', [])
    hdr_row = [
        Paragraph('Aseguradora / Plan', e['tabla_hdr']),
        Paragraph('Punto fuerte', e['tabla_hdr']),
        Paragraph('RC', e['tabla_hdr']),
        Paragraph('Parcial', e['tabla_hdr']),
        Paragraph('Total', e['tabla_hdr']),
        Paragraph('Auto sust.', e['tabla_hdr']),
        Paragraph('Prima anual', e['tabla_hdr']),
        Paragraph('Prima/mes', e['tabla_hdr']),
    ]
    filas = [hdr_row]
    for p in planes:
        mes = calcular_prima(p['prima_total'])['total'] / 12
        aseg_plan = Table([
            [Paragraph(p['aseguradora'], e['tabla_gray'])],
            [Paragraph(p['plan'], e['tabla_bold'])],
        ])
        aseg_plan.setStyle(TableStyle([
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),
        ]))
        filas.append([
            aseg_plan,
            mk_badge(p['ventaja_texto'], p['ventaja_tipo']),
            Paragraph(p.get('rc','—'), e['tabla_cel']),
            Paragraph('✓' if p.get('parcial') else '–', e['tabla_bold']),
            Paragraph('✓' if p.get('total') else '–', e['tabla_bold']),
            Paragraph(p.get('auto_sust','–'), e['tabla_cel']),
            Paragraph(f"$ {calcular_prima(p['prima_total'])['total']:,.2f}", e['tabla_bold']),
            Paragraph(f"$ {mes:,.2f}", e['tabla_cel']),
        ])

    cw = [doc.width*w for w in [0.22, 0.17, 0.08, 0.07, 0.07, 0.09, 0.14, 0.16]]
    tbl = Table(filas, colWidths=cw, repeatRows=1)
    row_styles = [
        ('BACKGROUND',(0,0),(-1,0),BLACK),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LGRAY]),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBELOW',(0,0),(-1,-1),0.3,GRAY),
        ('ALIGN',(2,0),(-1,-1),'CENTER'),
        ('ALIGN',(6,0),(-1,-1),'RIGHT'),
        ('ALIGN',(7,0),(-1,-1),'RIGHT'),
    ]
    for i, p in enumerate(planes):
        if p.get('recomendado'):
            row_styles += [
                ('LINEABOVE',(0,i+1),(-1,i+1),1.5,PURPLE),
                ('LINEBELOW',(0,i+1),(-1,i+1),1.5,PURPLE),
            ]
    tbl.setStyle(TableStyle(row_styles))
    story.append(tbl)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        '★ Borde púrpura = plan recomendado.  Ver páginas siguientes para el detalle completo de cada opción.',
        e['nota']))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRAY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'Comparativa referencial. Valores sujetos a verificación de datos del asegurado. Vigencia: 15 días calendario desde emisión.',
        e['nota']))

# ── Una hoja por plan ─────────────────────────────────────────────────────────
def pagina_detalle(story, plan, e, doc):
    story.append(PageBreak())

    # Altura útil disponible (H - topMargin - bottomMargin)
    # topMargin=63mm, bottomMargin=24mm → útil ≈ 841.89 - 178.6 - 68.0 = ~595 pt
    ALTURA_UTIL = H - 63*mm - 24*mm

    contenido = []

    # — Encabezado del plan —
    enc = Table([[
        Table([[Paragraph(plan['aseguradora'], e['plan_aseg'])],
               [Paragraph(plan['plan'], e['plan_tit'])]]),
        mk_badge(plan['ventaja_texto'], plan['ventaja_tipo']),
    ]], colWidths=[doc.width*0.75, doc.width*0.25])
    enc.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('ALIGN',(1,0),(-1,-1),'RIGHT'),
    ]))
    contenido.append(enc)
    contenido.append(HRFlowable(width='100%', thickness=1.5, color=PURPLE))
    contenido.append(Spacer(1, 3*mm))

    # — Bloque primas —
    c = calcular_prima(plan['prima_total'])
    prima_con_iva = c['total']
    mes_con_iva = prima_con_iva / 12

    # Tabla desglose de costos
    desglose_data = [
        [Paragraph('Concepto', e['tabla_hdr']), Paragraph('Valor', e['tabla_hdr'])],
        [Paragraph('Prima neta', e['tabla_cel']),           Paragraph(f"$ {c['prima_neta']:,.2f}", e['tabla_bold'])],
        [Paragraph('SCVS (3.5%)', e['tabla_cel']),          Paragraph(f"$ {c['scvs']:,.2f}", e['tabla_bold'])],
        [Paragraph('Seguro Campesino (0.5%)', e['tabla_cel']),Paragraph(f"$ {c['camp']:,.2f}", e['tabla_bold'])],
        [Paragraph('Derechos de emisión', e['tabla_cel']),  Paragraph(f"$ {c['emision']:,.2f}", e['tabla_bold'])],
        [Paragraph('Base imponible IVA', e['tabla_cel']),   Paragraph(f"$ {c['base']:,.2f}", e['tabla_bold'])],
        [Paragraph('IVA (15%)', e['tabla_cel']),            Paragraph(f"$ {c['iva']:,.2f}", e['tabla_bold'])],
        [Paragraph('Prima total', ParagraphStyle('pt2', fontName='Helvetica-Bold', fontSize=9, textColor=PURPLE, leading=12)),
         Paragraph(f"$ {c['total']:,.2f}", ParagraphStyle('pv2', fontName='Helvetica-Bold', fontSize=11, textColor=PURPLE, leading=14))],
    ]
    tbl_desglose = Table(desglose_data, colWidths=[doc.width*0.65, doc.width*0.35])
    tbl_desglose.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), BLACK),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[WHITE,LGRAY]),
        ('BACKGROUND',(0,-1),(-1,-1), colors.HexColor('#f3e5f5')),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,0),(-1,-1),0.3,GRAY),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),
    ]))
    contenido.append(tbl_desglose)
    contenido.append(Spacer(1, 2*mm))

    # Cuota mensual destacada
    tbl_p = Table([[
        Paragraph('Cuota mensual × 12 sin intereses', e['lbl']),
        Paragraph('Deducible parcial', e['lbl']),
    ],[
        Paragraph(f"$ {mes_con_iva:,.2f}/mes", e['prima_xl']),
        Paragraph(plan.get('deducible_corto','—'), e['prima_md']),
    ]], colWidths=[doc.width*0.60, doc.width*0.40])
    tbl_p.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),LGRAY),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('LINEAFTER',(0,0),(1,-1),0.5,GRAY),
    ]))
    contenido.append(tbl_p)
    contenido.append(Spacer(1, 3*mm))

    # — Coberturas + Asistencias en dos columnas para ahorrar espacio —
    cob_rows = [[Paragraph('Cobertura', e['tabla_hdr']),
                 Paragraph('Límite', e['tabla_hdr'])]]
    for nc, lim in plan.get('coberturas', []):
        cob_rows.append([Paragraph(nc, e['tabla_cel']),
                         Paragraph(lim, e['tabla_bold'])])
    tbl_cob = Table(cob_rows, colWidths=[doc.width*0.65, doc.width*0.35])
    tbl_cob.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),BLACK),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LGRAY]),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('LINEBELOW',(0,0),(-1,-1),0.3,GRAY),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),
    ]))

    # Deducible + asistencias apilados en columna derecha
    ded_asist = []
    ded_asist.append(Paragraph('Deducibles', e['seccion']))
    ded_asist.append(Spacer(1, 1*mm))
    ded_asist.append(Paragraph(plan.get('deducible','—'), e['nota']))
    if plan.get('asistencias'):
        ded_asist.append(Spacer(1, 3*mm))
        ded_asist.append(Paragraph('Asistencias incluidas', e['seccion']))
        ded_asist.append(Spacer(1, 1*mm))
        ded_asist.append(Paragraph(plan['asistencias'], e['tabla_cel']))

    contenido.append(Paragraph('Coberturas incluidas', e['seccion']))
    contenido.append(Spacer(1, 1.5*mm))
    contenido.append(tbl_cob)
    contenido.append(Spacer(1, 3*mm))
    for item in ded_asist:
        contenido.append(item)

    contenido.append(Spacer(1, 3*mm))
    contenido.append(HRFlowable(width='100%', thickness=0.5, color=GRAY))
    contenido.append(Spacer(1, 1.5*mm))
    contenido.append(Paragraph(
        'En caso de discrepancia prevalecen las condiciones generales y particulares de la póliza emitida.',
        e['nota']))

    # KeepInFrame fuerza que todo quepa en la altura disponible (shrink si es necesario)
    frame = KeepInFrame(doc.width, ALTURA_UTIL, contenido, mode='shrink')
    story.append(frame)

# ── Función principal ─────────────────────────────────────────────────────────
def generar_pdf(datos, output_path):
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
    e = E()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=63*mm, bottomMargin=24*mm)
    story = []
    pagina_resumen(story, datos, e, doc)
    for plan in datos.get('planes', []):
        pagina_detalle(story, plan, e, doc)
    doc.build(story, canvasmaker=lambda fn, **kw: BrandedCanvas(fn, logo_path, **kw))
    print(f"PDF generado: {output_path}")

# ── Datos de ejemplo ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    datos = {
        'nombre': 'Veronica Tobar Taylor', 'cedula': '1713919841',
        'telefono': '0989382370', 'correo': 'ramiro@ssasesores.com.ec',
        'placa': 'PFB-7622', 'marca': 'NISSAN', 'modelo': 'ROGUE',
        'anio': '2020', 'tipo': 'JEEP / SUV', 'uso': 'PERSONAL', 'valor': 24000.00,
        'planes': [
            {
                'aseguradora': 'AIG Metropolitana', 'plan': 'Full Cobertura',
                'ventaja_texto': 'Mayor cobertura total', 'ventaja_tipo': 'cobertura',
                'recomendado': True,
                'rc': '$40.000', 'parcial': True, 'total': True, 'auto_sust': '15/30 días',
                'prima_total': 985.93, 
                'deducible_corto': '10% VS / mín $250',
                'deducible': 'Parciales: 10% VS / 1% VA / mín $250 (el mayor).  Total daños: 15% VA.  Total robo: 15-20% VA según dispositivo.',
                'asistencias': 'Auxilio mecánico · Remolque · Avería leve · Descarga de batería · Ángel Guardián · Traslado ambulancia · Red talleres KPG · Asistencia legal 24/7 · Inspección a domicilio · No cobro R.A.S.A.',
                'coberturas': [
                    ('Responsabilidad civil – límite único combinado','$40.000'),
                    ('Pérdida parcial por daños','$24.000'),('Pérdida total por daños','$24.000'),
                    ('Pérdida parcial por robo','$24.000'),('Pérdida total por robo','$24.000'),
                    ('Gastos médicos por ocupante','$3.000'),('Accidentes personales por ocupante','$5.000'),
                    ('Grúa, transporte y protección','$300'),('Amparo jurídico','$1.000'),
                    ('Muerte accidental o incapacidad total','$10.000'),
                    ('Llave protegida','$150'),('Documentos protegidos','$100'),
                    ('Auto sustituto – parciales','15 días/evento'),('Auto sustituto – totales','30 días'),
                    ('Asistencias AIG MetroAssit','Incluido'),('Amparo patrimonial','$24.000'),
                ],
            },
            {
                'aseguradora': 'Sur One – Aseguradora del Sur', 'plan': 'Plan Plata',
                'ventaja_texto': 'Diferible 12 meses sin intereses', 'ventaja_tipo': 'flexibilidad',
                'recomendado': False,
                'rc': '$40.000', 'parcial': True, 'total': True, 'auto_sust': '15/30 días',
                'prima_total': 1080.00, 
                'deducible_corto': '$400 fijo',
                'deducible': 'Pérdidas parciales: $400 fijo.  Total daños: 15% VA.  Total robo: 20% VA.',
                'asistencias': 'Grúa · Auxilio vial · Paso de corriente · Cambio de llanta · Combustible · Cerrajería vial · Lavado express 1x/año (Quito/GYE/Cuenca) · Asistencia legal.',
                'coberturas': [
                    ('Responsabilidad civil','$40.000'),
                    ('Pérdida parcial daños/robo','$24.000'),('Pérdida total daños/robo','$24.000'),
                    ('Muerte accidental por ocupante','$5.000'),('Invalidez por ocupante','$5.000'),
                    ('Sepelio por ocupante','$500'),('Gastos médicos (ded. $40)','$2.500'),
                    ('Radio y parlantes','$1.500'),
                    ('Auto sustituto – parciales (> $1.550)','15 días'),
                    ('Auto sustituto – totales por robo','30 días'),('Amparo patrimonial','Incluido'),
                ],
            },
            {
                'aseguradora': 'Equisuiza', 'plan': 'Autoseguro Amparo Patrimonial',
                'ventaja_texto': 'RC más alta: $80.000', 'ventaja_tipo': 'cobertura',
                'recomendado': False,
                'rc': '$80.000', 'parcial': True, 'total': True, 'auto_sust': '10/20 días',
                'prima_total': 864.57, 
                'deducible_corto': 'Taller convenio mín $200',
                'deducible': 'Taller convenio: 10%/1%VA/mín $200.  Concesionario ≤2 años: mín $350.  Concesionario >2 años: mín $400.  Sin convenio: mín $400.  Robo sin disp. >$30k: 20% VA.',
                'asistencias': 'Conductor profesional sin límite · Ambulancia sin límite · Grúa 24/7 200km/3 eventos · Asistencia legal in situ · Reemplazo de llaves máx $200 · Gastos exequiales titular · Médica telefónica 24/7.',
                'coberturas': [
                    ('RC – daños a terceros','$80.000'),
                    ('Pérdida parcial/total por choque','Incluido'),
                    ('Pérdida parcial/total por robo','Incluido'),
                    ('Gastos médicos por ocupante','$3.000'),
                    ('Muerte accidental por ocupante','$5.000'),
                    ('Amparo patrimonial','Incluido'),
                    ('Auto sustituto – parciales (> $1.300)','10 días'),
                    ('Auto sustituto – totales','20 días'),
                    ('Reemplazo de llaves por robo','máx $200 / 1 evento'),
                    ('Gastos exequiales titular','Incluido'),
                    ('Asistencia médica telefónica 24/7','Incluido'),
                ],
            },
            {
                'aseguradora': 'AIG por Kilómetro', 'plan': 'Paquete 5.000 km – 6 meses',
                'ventaja_texto': 'Pagas solo lo que recorres', 'ventaja_tipo': 'economico',
                'recomendado': False,
                'rc': '$40.000', 'parcial': True, 'total': True, 'auto_sust': '10/20 días',
                'prima_total': 376.82, 
                'deducible_corto': '10% VS / mín $250',
                'deducible': 'Parciales: 10% VS / 1% VA / mín $250 (el mayor).  Total daños y robo: 15% VA.',
                'asistencias': 'Asistencia vial 24h · Ángel Guardián · APP de servicios · Red talleres KPG.',
                'coberturas': [
                    ('Duración del paquete','180 días / 6 meses'),
                    ('Kilómetros cubiertos','5.000 km'),
                    ('Responsabilidad civil','$40.000'),
                    ('Pérdida parcial por daños','$24.000'),('Pérdida total por daños','$24.000'),
                    ('Pérdida parcial por robo','$24.000'),('Pérdida total por robo','$24.000'),
                    ('Gastos médicos por ocupante','$3.000'),
                    ('Accidentes personales por ocupante','$5.000'),
                    ('Grúa y transporte','$200'),
                    ('Auto sustituto – parciales','10 días'),('Auto sustituto – totales','20 días'),
                ],
            },
        ]
    }
    generar_pdf(datos, '/mnt/user-data/outputs/propuesta_cotizacion.pdf')
