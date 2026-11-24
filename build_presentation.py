"""
Generador de la Presentación de Sustentación APF3 (13 Diapositivas)
Curso: Innovación y Transformación Digital (Sección 35036) - UTP 2026-2
Empresa: HURIOS RALLY E.I.R.L.
Diseño: Limpio, modular (tarjetas cuadradas en lugar de párrafos densos),
sin paréntesis de tiempos/rúbrica, sin flechas raras, con las imágenes
actualizadas del Informe Word (Anexos y Figuras) en gran tamaño y cierre ejecutivo.
"""
from pathlib import Path
from PIL import Image, ImageChops
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT_DIR = Path(__file__).resolve().parent.parent
ML_DIR = Path(__file__).resolve().parent
DOCX_MEDIA = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b\scratch\user_docx_extracted\word\media")
CROPPED_DIR = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b\scratch\cropped_media")
CROPPED_DIR.mkdir(parents=True, exist_ok=True)
LOGO_HURIOS = ROOT_DIR / "HuriosRally-Frontend" / "public" / "assets" / "imgs" / "Logo_Mejorado.png"

# Paleta ejecutiva de alto contraste sobre fondo claro
C_BG = RGBColor(248, 250, 252)         # #F8FAFC Fondo general claro
C_WHITE = RGBColor(255, 255, 255)      # #FFFFFF Tarjetas
C_NAVY = RGBColor(15, 23, 42)          # #0F172A Texto principal oscuro
C_SLATE = RGBColor(51, 65, 85)         # #334155 Texto secundario
C_MUTED = RGBColor(100, 116, 139)      # #64748B Etiquetas discretas
C_BLUE = RGBColor(11, 77, 162)         # #0B4DA2 Azul Hurios
C_BLUE_SOFT = RGBColor(239, 246, 255)  # #EFF6FF Azul suave para tarjetas destacadas
C_BLUE_DARK = RGBColor(15, 41, 74)     # #0F294A Azul profundo encabezados
C_MINT = RGBColor(82, 196, 154)        # #52C49A Verde menta portada
C_MINT_DARK = RGBColor(13, 148, 104)   # #0D9468 Verde esmeralda intenso
C_MINT_SOFT = RGBColor(236, 253, 245)  # #ECFDF5 Fondo esmeralda suave
C_AMBER = RGBColor(217, 119, 6)        # #D97706 Ámbar ejecutivo
C_AMBER_SOFT = RGBColor(255, 251, 235) # #FFFBEB Fondo ámbar suave
C_BORDER = RGBColor(203, 213, 225)     # #CBD5E1 Borde definido


def set_es_lang(run):
    """Configura el idioma del texto en español (Perú) para evitar subrayados rojos en PowerPoint."""
    try:
        rPr = run._r.get_or_add_rPr()
        rPr.set("lang", "es-PE")
    except Exception:
        pass


def set_slide_bg(slide, color=C_BG):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_speaker_notes(slide, text: str):
    slide.notes_slide.notes_text_frame.text = text


def add_polygon(slide, points: list, fill_color: RGBColor):
    x0, y0 = points[0]
    builder = slide.shapes.build_freeform(Inches(x0), Inches(y0))
    builder_pts = [(Inches(x), Inches(y)) for x, y in points[1:]]
    builder.add_line_segments(builder_pts, close=True)
    shape = builder.convert_to_shape()
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape


def prepare_image(img_path: Path, trim_white: bool = False) -> Path:
    if not img_path.exists() or not trim_white:
        return img_path
    out_path = CROPPED_DIR / f"trim_{img_path.name}"
    try:
        with Image.open(img_path) as im:
            rgb = im.convert("RGB")
            bg = Image.new("RGB", rgb.size, (255, 255, 255))
            diff = ImageChops.difference(rgb, bg)
            bbox = diff.getbbox()
            if bbox:
                pad = 12
                left = max(0, bbox[0] - pad)
                top = max(0, bbox[1] - pad)
                right = min(rgb.width, bbox[2] + pad)
                bottom = min(rgb.height, bbox[3] + pad)
                cropped = im.crop((left, top, right, bottom))
                cropped.save(out_path)
                return out_path
    except Exception:
        pass
    return img_path


def add_picture_fit(slide, img_path: Path, left: float, top: float, max_w: float, max_h: float, trim_white: bool = False):
    """Inserta una imagen maximizando su tamaño dentro del área disponible sin deformarla."""
    if not img_path.exists():
        return None
    final_path = prepare_image(img_path, trim_white=trim_white)
    with Image.open(final_path) as im:
        w_px, h_px = im.size
    ratio = w_px / float(h_px)
    if max_w / ratio <= max_h:
        w = max_w
        h = max_w / ratio
    else:
        h = max_h
        w = max_h * ratio
    x = left + (max_w - w) / 2.0
    y = top + (max_h - h) / 2.0
    return slide.shapes.add_picture(str(final_path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))


def add_header(slide, slide_num: int, block_label: str, title: str):
    """Encabezado limpio sin paréntesis de tiempos ni referencias de rúbrica."""
    set_slide_bg(slide, C_BG)

    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_BLUE
    bar.line.fill.background()

    tb_k = slide.shapes.add_textbox(Inches(0.55), Inches(0.22), Inches(11.0), Inches(0.26))
    tf_k = tb_k.text_frame
    tf_k.margin_left = 0
    tf_k.margin_top = 0
    pk = tf_k.paragraphs[0]
    rk = pk.add_run()
    rk.text = block_label.upper()
    rk.font.name = "Arial"
    rk.font.size = Pt(10)
    rk.font.bold = True
    rk.font.color.rgb = C_BLUE
    set_es_lang(rk)

    tb_t = slide.shapes.add_textbox(Inches(0.55), Inches(0.46), Inches(12.2), Inches(0.48))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = 0
    tf_t.margin_top = 0
    pt = tf_t.paragraphs[0]
    rt = pt.add_run()
    rt.text = title
    rt.font.name = "Arial"
    rt.font.size = Pt(21.5)
    rt.font.bold = True
    rt.font.color.rgb = C_NAVY
    set_es_lang(rt)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(1.02), Inches(12.23), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = C_BORDER
    line.line.fill.background()

    tb_f = slide.shapes.add_textbox(Inches(0.55), Inches(7.15), Inches(12.23), Inches(0.24))
    tf_f = tb_f.text_frame
    tf_f.margin_left = 0
    pf = tf_f.paragraphs[0]
    pf.alignment = PP_ALIGN.RIGHT
    rf = pf.add_run()
    rf.text = f"Hurios Rally E.I.R.L.   |   {slide_num} / 13"
    rf.font.name = "Arial"
    rf.font.size = Pt(9.5)
    rf.font.color.rgb = C_MUTED
    set_es_lang(rf)


def add_box(slide, left: float, top: float, width: float, height: float,
            title: str = "", bg_color=C_WHITE, border_color=C_BORDER, title_color=C_NAVY):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = bg_color
    box.line.color.rgb = border_color
    box.line.width = Pt(1)

    if title:
        tb = slide.shapes.add_textbox(Inches(left + 0.18), Inches(top + 0.12), Inches(width - 0.36), Inches(0.34))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = 0
        tf.margin_top = 0
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = title
        r.font.name = "Arial"
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = title_color
        set_es_lang(r)
    return box


def add_feature_card(slide, left: float, top: float, width: float, height: float,
                     title: str, body: str, accent_color=C_BLUE, bg_color=C_WHITE):
    """Tarjeta cuadrada/modular con borde izquierdo de color para reemplazar párrafos de texto."""
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = C_BORDER
    card.line.width = Pt(1)

    # Barra lateral izquierda integrada al borde de la tarjeta
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(0.08), Inches(height))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent_color
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(left + 0.20), Inches(top + 0.12), Inches(width - 0.32), Inches(height - 0.20))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_top = 0

    p1 = tf.paragraphs[0]
    p1.space_after = Pt(4)
    r1 = p1.add_run()
    r1.text = title
    r1.font.name = "Arial"
    r1.font.size = Pt(12.5)
    r1.font.bold = True
    r1.font.color.rgb = C_NAVY
    set_es_lang(r1)

    p2 = tf.add_paragraph()
    r2 = p2.add_run()
    r2.text = body
    r2.font.name = "Arial"
    r2.font.size = Pt(11.2)
    r2.font.color.rgb = C_SLATE
    set_es_lang(r2)


def add_metric(slide, left: float, top: float, width: float, height: float,
               label: str, value: str, sub: str, accent_color=C_BLUE, bg_color=C_WHITE):
    add_box(slide, left, top, width, height, "", bg_color, C_BORDER)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(0.08), Inches(height))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent_color
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(left + 0.20), Inches(top + 0.12), Inches(width - 0.32), Inches(height - 0.20))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_top = 0

    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    r1.text = label.upper()
    r1.font.name = "Arial"
    r1.font.size = Pt(10)
    r1.font.bold = True
    r1.font.color.rgb = C_MUTED
    set_es_lang(r1)

    p2 = tf.add_paragraph()
    p2.space_before = Pt(3)
    p2.space_after = Pt(2)
    r2 = p2.add_run()
    r2.text = value
    r2.font.name = "Arial"
    r2.font.size = Pt(22)
    r2.font.bold = True
    r2.font.color.rgb = accent_color
    set_es_lang(r2)

    p3 = tf.add_paragraph()
    r3 = p3.add_run()
    r3.text = sub
    r3.font.name = "Arial"
    r3.font.size = Pt(10.5)
    r3.font.color.rgb = C_SLATE
    set_es_lang(r3)


def style_table(table, headers: list, rows: list, col_widths: list, font_size: float = 11.0):
    for i, w in enumerate(col_widths):
        table.columns[i].width = Inches(w)

    for c_idx, h_text in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_BLUE_DARK
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = h_text
        r.font.name = "Arial"
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = C_WHITE
        set_es_lang(r)

    for r_idx, row_data in enumerate(rows):
        bg_row = C_WHITE if r_idx % 2 == 0 else RGBColor(241, 245, 249)
        for c_idx, val in enumerate(row_data):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_row
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.name = "Arial"
            r.font.size = Pt(font_size)
            r.font.bold = (c_idx == 0)
            r.font.color.rgb = C_NAVY if c_idx == 0 else C_SLATE
            set_es_lang(r)


def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ==========================================================================
    # SLIDE 1: CARÁTULA OFICIAL
    # ==========================================================================
    s1 = prs.slides.add_slide(blank)
    set_slide_bg(s1, C_BG)

    add_polygon(s1, [
        (0.0, 0.0),
        (2.40, 0.0),
        (6.80, 7.5),
        (0.0, 7.5),
    ], RGBColor(238, 242, 246))

    add_polygon(s1, [
        (0.0, 0.22),
        (0.0, 1.48),
        (1.62, 3.32),
        (2.74, 3.32),
    ], C_BLUE)

    add_polygon(s1, [
        (0.96, 0.88),
        (2.22, 0.88),
        (4.15, 3.06),
        (4.15, 4.18),
    ], C_MINT)

    logo_box = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.15), Inches(4.30), Inches(2.65), Inches(2.65))
    logo_box.fill.solid()
    logo_box.fill.fore_color.rgb = C_WHITE
    logo_box.line.color.rgb = C_BORDER
    logo_box.line.width = Pt(1)
    add_picture_fit(s1, LOGO_HURIOS, 1.25, 4.40, 2.45, 2.45)

    tb_title = s1.shapes.add_textbox(Inches(5.15), Inches(1.25), Inches(7.5), Inches(1.90))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = 0
    p_t1 = tf_title.paragraphs[0]
    r_t1 = p_t1.add_run()
    r_t1.text = "HURIOS RALLY"
    r_t1.font.name = "Arial"
    r_t1.font.size = Pt(44)
    r_t1.font.bold = True
    r_t1.font.italic = True
    r_t1.font.color.rgb = C_NAVY
    set_es_lang(r_t1)

    p_t2 = tf_title.add_paragraph()
    r_t2 = p_t2.add_run()
    r_t2.text = "E.I.R.L."
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(42)
    r_t2.font.bold = True
    r_t2.font.italic = True
    r_t2.font.color.rgb = C_NAVY
    set_es_lang(r_t2)

    tb_sub = s1.shapes.add_textbox(Inches(5.15), Inches(3.15), Inches(7.6), Inches(0.65))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = 0
    p_sub = tf_sub.paragraphs[0]
    r_sub = p_sub.add_run()
    r_sub.text = "Agente de ventas por WhatsApp con Inteligencia Artificial"
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(20)
    r_sub.font.italic = True
    r_sub.font.color.rgb = C_BLUE
    set_es_lang(r_sub)

    tb_int = s1.shapes.add_textbox(Inches(5.30), Inches(4.55), Inches(7.2), Inches(2.10))
    tf_int = tb_int.text_frame
    tf_int.word_wrap = True
    tf_int.margin_left = 0

    p_hdr = tf_int.paragraphs[0]
    p_hdr.space_after = Pt(8)
    r_hdr = p_hdr.add_run()
    r_hdr.text = "Integrantes:"
    r_hdr.font.name = "Arial"
    r_hdr.font.size = Pt(17)
    r_hdr.font.bold = True
    r_hdr.font.color.rgb = C_NAVY
    set_es_lang(r_hdr)

    for member in [
        "Taypicahuana Montalvo, Renzo Andre",
        "Gutierrez Cuellar, Josué Ángel",
        "Morales Carlos, Edu",
    ]:
        pm = tf_int.add_paragraph()
        pm.space_after = Pt(6)
        rm = pm.add_run()
        rm.text = f"-   {member}"
        rm.font.name = "Arial"
        rm.font.size = Pt(16.5)
        rm.font.color.rgb = C_SLATE
        set_es_lang(rm)

    add_speaker_notes(s1, (
        "Expositor: Renzo Taypicahuana.\n"
        "Presentación del equipo y del proyecto: Agente de ventas por WhatsApp con Inteligencia Artificial para HURIOS RALLY E.I.R.L."
    ))

    # ==========================================================================
    # SLIDE 2: CONTINUIDAD DEL PROYECTO Y PROBLEMA ML (TARJETAS MODULARES)
    # ==========================================================================
    s2 = prs.slides.add_slide(blank)
    add_header(s2, 2, "Bloque 1 · Contexto y Definición del Problema", "1. Evolución del Proyecto y Formulación del Problema ML")

    # 3 tarjetas superiores de continuidad
    add_feature_card(
        s2, 0.55, 1.18, 3.92, 1.55,
        "1. Diagnóstico en APF1",
        "Demora de 12 a 15 min en el día y hasta 8 h en la noche, perdiendo entre 35% y 40% de las ventas nocturnas en Comas.",
        C_BLUE
    )
    add_feature_card(
        s2, 4.70, 1.18, 3.92, 1.55,
        "2. Ecosistema MVP en APF2",
        "Tienda web en React, backend Spring Boot, catálogo real de 48 repuestos en PostgreSQL y contrato de datos de 12 campos.",
        C_MINT_DARK
    )
    add_feature_card(
        s2, 8.85, 1.18, 3.93, 1.55,
        "3. Solución ML en APF3",
        "Clasificación supervisada multiclase en 4 categorías operativas donde cada fila representa una consulta entrante.",
        C_NAVY
    )

    # Frase formal obligatoria
    add_box(s2, 0.55, 2.90, 12.23, 1.32, "Definición Formal del Problema de Machine Learning", C_BLUE_SOFT, C_BLUE, C_BLUE)
    tb_f = s2.shapes.add_textbox(Inches(0.75), Inches(3.32), Inches(11.85), Inches(0.80))
    tf_f = tb_f.text_frame
    tf_f.word_wrap = True
    pf = tf_f.paragraphs[0]
    rf = pf.add_run()
    rf.text = (
        "“Para el administrador y vendedores de HURIOS RALLY E.I.R.L., el modelo clasificará la intención de cada "
        "consulta en WhatsApp y Web (COTIZACION, CONSULTA_TECNICA, ESTADO_PEDIDO o SPAM) para responder las 24 horas "
        "con stock real de PostgreSQL y priorizar pagos Yape o Plin, superando la meta de F1-Macro mayor o igual a 0.85.”"
    )
    rf.font.name = "Arial"
    rf.font.size = Pt(12)
    rf.font.italic = True
    rf.font.color.rgb = C_NAVY
    set_es_lang(rf)

    # 4 tarjetas cuadradas inferiores (Variables y Costo de Errores sin párrafos largos)
    add_feature_card(
        s2, 0.55, 4.40, 2.90, 2.55,
        "Variable Objetivo (Y)",
        "Categoría de intención dividida en 4 clases balanceadas: Cotización (27.7%), Consulta Técnica (24.6%), Estado de Pedido (24.4%) y Spam (23.3%).",
        C_BLUE
    )
    add_feature_card(
        s2, 3.66, 4.40, 2.90, 2.55,
        "Variables Predictoras (X)",
        "Texto vectorizado con TF-IDF (1,200 términos), hora del día, indicador fuera de horario y 6 conteos de palabras clave del rubro.",
        C_BLUE_DARK
    )
    add_feature_card(
        s2, 6.77, 4.40, 2.90, 2.55,
        "Error Más Costoso",
        "Falso Positivo en SPAM: enviar a no deseados a un cliente real que busca comprar un cilindro o confirmar su pago Yape.",
        C_BLUE
    )
    add_feature_card(
        s2, 9.88, 4.40, 2.90, 2.55,
        "Regla de Protección",
        "Se exige Precisión de 100% en SPAM. Si la confianza de una predicción es menor a 65%, el chat pasa a un asesor humano.",
        C_MINT_DARK
    )

    add_speaker_notes(s2, (
        "Expositor: Renzo Taypicahuana.\n"
        "Explicar la continuidad desde APF1 y APF2 hacia el clasificador multiclase y por qué proteger contra Falsos Positivos en SPAM es crítico."
    ))

    # ==========================================================================
    # SLIDE 3: DATASET Y AUDITORÍA DE COHERENCIA
    # ==========================================================================
    s3 = prs.slides.add_slide(blank)
    add_header(s3, 3, "Bloque 2 · Dataset y Calidad de Datos", "2. Origen del Dataset y Auditoría de Coherencia")

    add_metric(s3, 0.55, 1.16, 2.90, 1.15, "Volumen Total", "520 × 13", "Supera mínimo de 500 filas", C_BLUE)
    add_metric(s3, 3.66, 1.16, 2.90, 1.15, "Consultas Reales", "130 (25%)", "WhatsApp y Web (Ago a Oct)", C_MINT_DARK)
    add_metric(s3, 6.77, 1.16, 2.90, 1.15, "Consultas Simuladas", "390 (75%)", "Precios reales PostgreSQL", C_NAVY)
    add_metric(s3, 9.88, 1.16, 2.90, 1.15, "Auditoría de Reglas", "0 Errores", "Ticket promedio S/ 183.40", C_MINT_DARK)

    headers_c = ["Criterio de Coherencia", "Qué se Verifica en el Dataset", "Evidencia Cuantitativa Auditada"]
    rows_c = [
        ["1. Escala del negocio", "Volumen de 75 días y precios acordes al almacén en Comas.", "Ticket medio S/ 183.40 (S/ 15 a S/ 980); 43.3% en horario nocturno."],
        ["2. Rangos y unidades", "Validación de precios, horas del día (0 a 23) y textos.", "0 valores negativos, 0 fuera de rango y 0 celdas vacías."],
        ["3. Consistencia temporal", "Respuesta del bot posterior al mensaje y regla horaria.", "0 respuestas anteriores al mensaje y 0 contradicciones de horario."],
        ["4. Relaciones de negocio", "Asociación entre vocabulario técnico/comercial y la clase.", "3 relaciones verificadas en cotización, consulta técnica y pedidos."],
        ["5. Nivel de señal realista", "Comportamiento intermedio entre azar (0.25) y perfección.", "Línea base obtiene F1 = 0.2688 y SVM alcanza F1 = 0.9393."],
        ["6. Trazabilidad con APF2", "Mismos 12 campos del Contrato de Datos más columna origen.", "13 columnas verificadas con anonimización UUID v4."],
        ["7. Homogeneidad real/simulado", "Comparación de longitud y monto entre ambos orígenes.", "Reales: 124.4 caracteres | Simulados: 123.5 caracteres."],
    ]
    tbl_c = s3.shapes.add_table(len(rows_c) + 1, 3, Inches(0.55), Inches(2.48), Inches(12.23), Inches(4.50))
    style_table(tbl_c.table, headers_c, rows_c, [2.80, 4.83, 4.60], font_size=10.8)

    add_speaker_notes(s3, (
        "Expositor: Josué Gutierrez.\n"
        "Explicar la composición del dataset (130 reales + 390 simulados) y el cumplimiento de los 7 criterios de coherencia."
    ))

    # ==========================================================================
    # SLIDE 4: EDA CON GRÁFICAS GRANDES DEL INFORME + TARJETAS MODULARES
    # ==========================================================================
    s4 = prs.slides.add_slide(blank)
    add_header(s4, 4, "Bloque 2 · Análisis Exploratorio y Preprocesamiento", "3. Gráficas del Análisis Exploratorio y Preparación de Datos")

    # Gráficas del informe (image2.png y image3.png) en tamaño grande (4.25 pulgadas de alto)
    add_box(s4, 0.55, 1.15, 6.00, 4.28, "Figura 1: Balance de Clases y Distribución por Franja Horaria")
    add_picture_fit(s4, DOCX_MEDIA / "image2.png", 0.65, 1.55, 5.80, 3.78, trim_white=True)

    add_box(s4, 6.78, 1.15, 6.00, 4.28, "Figura 2: Outliers de Longitud y Matriz de Correlaciones")
    add_picture_fit(s4, DOCX_MEDIA / "image3.png", 6.88, 1.55, 5.80, 3.78, trim_white=True)

    # 4 tarjetas cuadradas en la franja inferior (sin flechas raras ni párrafos largos)
    add_feature_card(
        s4, 0.55, 5.58, 2.90, 1.42,
        "Demanda Nocturna (43.3%)",
        "Confirma que el pico de mensajes ocurre entre las 19:00 y 23:00 horas.",
        C_BLUE
    )
    add_feature_card(
        s4, 3.66, 5.58, 2.90, 1.42,
        "Conservación de Outliers",
        "Los mensajes largos son consultas técnicas o publicidad y se escalan con StandardScaler.",
        C_MINT_DARK
    )
    add_feature_card(
        s4, 6.77, 5.58, 2.90, 1.42,
        "Normalización de Jerga",
        "Estandariza términos como “bajajita” por “bajaj torito” y “yapear” por “pago yape”.",
        C_BLUE
    )
    add_feature_card(
        s4, 9.88, 5.58, 2.90, 1.42,
        "Partición 80 / 20 sin Fuga",
        "416 filas para entrenamiento y 104 para prueba. El TF-IDF se ajusta solo en entrenamiento.",
        C_NAVY
    )

    add_speaker_notes(s4, (
        "Expositor: Josué Gutierrez.\n"
        "Interpretar las Figuras 1 y 2 del informe y explicar la normalización de jerga peruana y la partición 80/20."
    ))

    # ==========================================================================
    # SLIDE 5: LÍNEA BASE Y COMPARACIÓN DE LOS 4 MODELOS
    # ==========================================================================
    s5 = prs.slides.add_slide(blank)
    add_header(s5, 5, "Bloque 3 · Comparación de Modelos Supervisados", "4. Evaluación contra Línea Base y 4 Algoritmos de Clasificación")

    headers_m = ["Modelo Evaluado", "Configuración Óptima", "CV F1-Macro", "Train F1", "Test Acc.", "Test Prec.", "Test Recall", "Test F1-Macro"]
    rows_m = [
        ["0. Línea Base (Dummy)", "Estrategia estratificada al azar", "0.2423", "0.2512", "0.2788", "0.2692", "0.2689", "0.2688"],
        ["1. SVM Lineal (Seleccionado)", "Kernel lineal, C = 0.3", "0.9422", "0.9855", "0.9423", "0.9403", "0.9396", "0.9393"],
        ["2. Regresión Logística", "C = 1.0, optimizador lbfgs", "0.9469", "0.9927", "0.9423", "0.9403", "0.9396", "0.9393"],
        ["3. Random Forest", "150 árboles, prof. máx. = 12", "0.9397", "0.9928", "0.9327", "0.9367", "0.9284", "0.9293"],
        ["4. K-Nearest Neighbors", "13 vecinos, peso por distancia", "0.9224", "1.0000", "0.9231", "0.9218", "0.9219", "0.9209"],
    ]
    tbl_m = s5.shapes.add_table(len(rows_m) + 1, 8, Inches(0.55), Inches(1.22), Inches(12.23), Inches(3.15))
    style_table(tbl_m.table, headers_m, rows_m, [2.50, 2.43, 1.25, 1.10, 1.15, 1.15, 1.15, 1.50], font_size=10.8)

    # 3 tarjetas cuadradas en la parte inferior para explicar la elección sin bloques densos
    add_feature_card(
        s5, 0.55, 4.62, 3.92, 2.30,
        "Mejora de +67.05 Puntos sobre el Azar",
        "La línea base obtiene apenas 0.2688 de F1-Macro. Los 4 modelos supervisados superan 0.9200 bajo la misma partición de datos.",
        C_BLUE
    )
    add_feature_card(
        s5, 4.70, 4.62, 3.92, 2.30,
        "Ventaja del Hiperplano Lineal",
        "Al trabajar con 1,200 términos TF-IDF, los modelos de margen lineal (SVM y Regresión Logística) separan mejor las clases que KNN o árboles.",
        C_MINT_DARK
    )
    add_feature_card(
        s5, 8.85, 4.62, 3.93, 2.30,
        "Por qué Gana SVM Lineal (C = 0.3)",
        "Empata en el máximo F1 en prueba (0.9393), pero presenta el menor sobreajuste entre entrenamiento y prueba (+0.0462) y menor varianza.",
        C_BLUE, C_BLUE_SOFT
    )

    add_speaker_notes(s5, (
        "Expositor: Edu Morales.\n"
        "Explicar la tabla comparativa de los 4 modelos frente al DummyClassifier y por qué se seleccionó SVM Lineal (C=0.3)."
    ))

    # ==========================================================================
    # SLIDE 6: HIPERPARÁMETROS Y VIABILIDAD (DISEÑO EN CUADROS MODULARES)
    # ==========================================================================
    s6 = prs.slides.add_slide(blank)
    add_header(s6, 6, "Bloque 3 · Control de Sobreajuste y Despliegue", "5. Ajuste de Hiperparámetros y Viabilidad en Producción")

    # Mitad izquierda: Título de sección + 4 tarjetas cuadradas (2x2) en lugar de lista larga
    add_box(s6, 0.55, 1.18, 5.95, 0.48, "Estrategia de Control de Sobreajuste en Entrenamiento", C_BLUE_SOFT, C_BLUE, C_BLUE)

    add_feature_card(
        s6, 0.55, 1.80, 2.88, 2.45,
        "1. Validación 5-Fold",
        "GridSearchCV ejecutado únicamente sobre las 416 filas de entrenamiento, manteniendo intactas las 104 filas de prueba.",
        C_BLUE
    )
    add_feature_card(
        s6, 3.62, 1.80, 2.88, 2.45,
        "2. Regularización SVM",
        "El parámetro C = 0.3 penaliza coeficientes altos en palabras poco frecuentes, reduciendo la brecha Train-Test a +0.0462.",
        C_MINT_DARK
    )
    add_feature_card(
        s6, 0.55, 4.45, 2.88, 2.45,
        "3. Poda en Árboles",
        "En Random Forest se limitó la profundidad máxima a 12 niveles (150 árboles) para evitar memorizar el conjunto de entrenamiento.",
        C_NAVY
    )
    add_feature_card(
        s6, 3.62, 4.45, 2.88, 2.45,
        "4. Suavizado en KNN",
        "Se configuró un vecindario de k = 13 vecinos ponderados por distancia inversa para reducir sensibilidad al ruido léxico.",
        C_BLUE_DARK
    )

    # Mitad derecha: Viabilidad técnica en tarjetas cuadradas (2x2 KPIs + tarjeta inferior)
    add_box(s6, 6.83, 1.18, 5.95, 0.48, "Viabilidad Técnica de Despliegue en Render Cloud", C_BLUE_SOFT, C_BLUE, C_BLUE)

    add_metric(s6, 6.83, 1.80, 2.88, 1.55, "Peso del Artefacto", "86 KB", "Archivo .joblib serializado", C_BLUE)
    add_metric(s6, 9.90, 1.80, 2.88, 1.55, "Latencia en CPU", "3.2 ms", "1.31 s incluyendo consulta SQL", C_MINT_DARK)
    add_metric(s6, 6.83, 3.52, 2.88, 1.55, "Consumo de RAM", "< 45 MB", "Apto para plan gratuito (512 MB)", C_NAVY)
    add_metric(s6, 9.90, 3.52, 2.88, 1.55, "Costo por Inferencia", "S/ 0.00", "Sin cobro por token ni GPU", C_MINT_DARK)

    add_feature_card(
        s6, 6.83, 5.25, 5.95, 1.65,
        "Reentrenamiento Rápido y Continuidad Operativa",
        "El script train_pipeline.py regenera y valida el modelo completo en 15 segundos. El microservicio cuenta con endpoint /health y reconexión automática de WhatsApp.",
        C_BLUE, C_WHITE
    )

    add_speaker_notes(s6, (
        "Expositor: Edu Morales.\n"
        "Explicar los 4 controles contra el sobreajuste a la izquierda y los 4 indicadores de viabilidad en Render a la derecha."
    ))

    # ==========================================================================
    # SLIDE 7: EVALUACIÓN EN PRUEBA Y MATRIZ DE CONFUSIÓN GRANDE
    # ==========================================================================
    s7 = prs.slides.add_slide(blank)
    add_header(s7, 7, "Bloque 4 · Evaluación en Conjunto de Prueba", "6. Resultados por Clase y Matriz de Confusión del Modelo")

    # Figura 3 del informe mucho más grande y recortada de márgenes blancos
    add_box(s7, 0.55, 1.15, 7.55, 5.82, "Figura 3: Desempeño Comparativo y Matriz de Confusión (SVM)")
    add_picture_fit(s7, DOCX_MEDIA / "image4.png", 0.68, 1.58, 7.30, 5.25, trim_white=True)

    # Derecha: Tabla de métricas por clase + 2 tarjetas de lectura rápida
    add_box(s7, 8.28, 1.15, 4.50, 3.25, "Métricas en Prueba (104 Casos)")
    headers_cl = ["Categoría", "Prec.", "Recall", "F1", "Aciertos"]
    rows_cl = [
        ["COTIZACION", "0.964", "0.931", "0.947", "27 / 29"],
        ["CONSULTA_TECNICA", "0.893", "0.962", "0.926", "25 / 26"],
        ["ESTADO_PEDIDO", "0.923", "0.960", "0.941", "24 / 25"],
        ["SPAM", "1.000", "0.917", "0.957", "22 / 24"],
        ["PROMEDIO MACRO", "0.940", "0.940", "0.939", "98 / 104"],
    ]
    tbl_cl = s7.shapes.add_table(len(rows_cl) + 1, 5, Inches(8.42), Inches(1.62), Inches(4.22), Inches(2.60))
    style_table(tbl_cl.table, headers_cl, rows_cl, [1.46, 0.66, 0.66, 0.66, 0.78], font_size=9.6)

    add_feature_card(
        s7, 8.28, 4.55, 4.50, 1.15,
        "Cero Clientes Perdidos en SPAM",
        "Precisión de 1.000 en SPAM: ningún cliente real fue enviado por error a la bandeja de no deseados.",
        C_BLUE
    )
    add_feature_card(
        s7, 8.28, 5.82, 4.50, 1.15,
        "Alta Captura Comercial (94.2% Exactitud)",
        "98 aciertos de 104 casos, destacando 96.2% de Recall en dudas técnicas y 96.0% en pagos.",
        C_BLUE_DARK
    )

    add_speaker_notes(s7, (
        "Expositor: Edu Morales.\n"
        "Analizar la Figura 3 del informe y la tabla por clase: 98 aciertos de 104 y Precisión de 100% en SPAM."
    ))

    # ==========================================================================
    # SLIDE 8: ANÁLISIS DE CASOS DE ERROR EN TEST SET
    # ==========================================================================
    s8 = prs.slides.add_slide(blank)
    add_header(s8, 8, "Bloque 4 · Análisis de Errores y Límites del Modelo", "7. Auditoría de los 6 Casos de Error en Prueba e Hipótesis")

    headers_err = ["ID Caso", "Mensaje Evaluado en Prueba", "Clase Real", "Predicción", "Conf.", "Hipótesis del Error y Mitigación"]
    rows_err = [
        ["4f1c4b23 (Real)", "“...ese repuesto le hace a mi Torito 2018 o tienes en stock otro que le calce y a cuánto”", "TECNICA", "COTIZACION", "0.54", "Doble intención (calce y precio). Como confianza < 0.65, envía stock y deriva a asesor."],
        ["7b8d29a1 (Sim.)", "“...el cilindro que me cotizaste ayer ya te lo yapeé, confírmame si le da al Bajaj FL”", "PEDIDO", "TECNICA", "0.58", "Mezcla pago con duda de compatibilidad. El flujo de opción 3 valida el comprobante."],
        ["91a4e0c2 (Real)", "“...tienes rodaje trasero para TVS King y dime si ya salió mi envío anterior”", "COTIZACION", "PEDIDO", "0.61", "Dos solicitudes en una frase; el peso de 'salió mi envío' inclinó la predicción."],
        ["c3e910f4 (Sim.)", "“...vendes repuestos al por mayor para taller en Carabayllo, mándame lista de precios”", "SPAM", "COTIZACION", "0.63", "Falso negativo B2B por usar 'lista de precios'. Preferible antes que bloquear un taller."],
        ["d8f201a9 (Sim.)", "“...te dejé el voucher del Plin por las zapatas, a cuánto me dejas el tambor trasero”", "COTIZACION", "PEDIDO", "0.59", "Recompra tras pago. Con confianza < 0.65 se marca para atención prioritaria."],
        ["e5a712b0 (Sim.)", "“...somos distribuidores de lubricantes 20W50 para mototaxis, precio de fábrica”", "SPAM", "COTIZACION", "0.57", "Proveedor mayorista usando palabras del catálogo ('20W50', 'precio')."],
    ]
    tbl_err = s8.shapes.add_table(len(rows_err) + 1, 6, Inches(0.55), Inches(1.18), Inches(12.23), Inches(4.35))
    style_table(tbl_err.table, headers_err, rows_err, [1.25, 3.88, 1.05, 1.15, 0.68, 4.22], font_size=9.8)

    add_feature_card(
        s8, 0.55, 5.68, 5.95, 1.30,
        "Límite de Dominio y Volumen (520 Registros)",
        "Entrenado con 130 casos reales y 390 simulados de repuestos Bajaj y TVS; para otras líneas automotrices requiere reentrenamiento.",
        C_BLUE_DARK
    )
    add_feature_card(
        s8, 6.83, 5.68, 5.95, 1.30,
        "Mitigación de Mensajes Cortos o Ambiguos",
        "Los 6 errores ocurren con confianza baja (0.54 a 0.63). El menú numerado (Opciones 1 a 4) y el umbral de 0.65 evitan respuestas erróneas.",
        C_BLUE
    )

    add_speaker_notes(s8, (
        "Expositor: Edu Morales.\n"
        "Explicar los 6 casos donde el modelo se equivoca en Test y cómo el umbral de confianza de 0.65 protege la operación."
    ))

    # ==========================================================================
    # SLIDE 9: DEMOSTRACIÓN EN VIVO CON LAS IMÁGENES DEL ANEXO DEL INFORME
    # ==========================================================================
    s9 = prs.slides.add_slide(blank)
    add_header(s9, 9, "Bloque 4 · Demostración en Vivo en WhatsApp y Web", "8. Predicción con el Archivo .joblib y Evidencia del Sistema")

    # Columna izquierda arriba: Inferencia reproducible con .joblib (sin pisar el título)
    add_box(s9, 0.55, 1.15, 5.35, 2.75, "Carga Directa de modelo_intenciones_hurios.joblib")
    code_box = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.73), Inches(1.58), Inches(4.98), Inches(2.15))
    code_box.fill.solid()
    code_box.fill.fore_color.rgb = C_NAVY
    code_box.line.fill.background()
    tf_c = code_box.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = Inches(0.14)
    tf_c.margin_top = Inches(0.10)
    pc = tf_c.paragraphs[0]
    rc = pc.add_run()
    rc.text = (
        "artefacto = joblib.load('modelo_intenciones_hurios.joblib')\n"
        "nuevo_msg = {\n"
        "  'texto_mensaje': 'Buenas noches, tienes kit de pistón '\n"
        "                   'standard para Torito Bajaj 4T y stock?',\n"
        "  'hora_del_dia': 21, 'es_fuera_horario': 1\n"
        "}\n"
        "# SALIDA EN 3.2 ms:\n"
        "intencion_predicha : 'COTIZACION' (Confianza: 96.02%)"
    )
    rc.font.name = "Consolas"
    rc.font.size = Pt(9.5)
    rc.font.color.rgb = RGBColor(226, 232, 240)
    set_es_lang(rc)

    # Columna izquierda abajo: Captura del Bot de WhatsApp del Anexo del Informe (image8.png)
    add_box(s9, 0.55, 4.02, 5.35, 2.98, "Anexo del Informe: Bot WhatsApp (+51 937 395 986)")
    add_picture_fit(s9, DOCX_MEDIA / "image8.png", 0.68, 4.44, 5.10, 2.45)

    # Columna derecha completa: Gráficas BI y Bandeja del Anexo del Informe (image11.png + image10.png)
    add_box(s9, 6.10, 1.15, 6.68, 5.85, "Anexo del Informe: Clasificador y Analítica WhatsApp en Vivo")
    add_picture_fit(s9, DOCX_MEDIA / "image11.png", 6.24, 1.56, 6.40, 2.48, trim_white=True)
    add_picture_fit(s9, DOCX_MEDIA / "image10.png", 6.24, 4.12, 6.40, 2.76, trim_white=True)

    add_speaker_notes(s9, (
        "Expositor: Edu Morales.\n"
        "Mostrar la predicción sobre un registro nuevo con el archivo .joblib y las capturas actualizadas del Anexo del Informe: "
        "el bot de WhatsApp cotizando con stock real y el panel de analítica con gráficas del modelo."
    ))

    # ==========================================================================
    # SLIDE 10: IMPACTO DE NEGOCIO Y FIGURA 4 GRANDE
    # ==========================================================================
    s10 = prs.slides.add_slide(blank)
    add_header(s10, 10, "Bloque 5 · Impacto Comercial e Interpretabilidad", "9. Resultados para el Negocio y Variables más Importantes")

    add_metric(s10, 0.55, 1.15, 3.92, 1.15, "Tiempo de Respuesta", "De 15 min a 1.31 s", "Atención automática las 24 horas", C_BLUE)
    add_metric(s10, 4.70, 1.15, 3.92, 1.15, "Ventas Nocturnas Recuperadas", "S/ 2,250 a 2,850", "Ingresos mensuales estimados", C_MINT_DARK)
    add_metric(s10, 8.85, 1.15, 3.93, 1.15, "Tiempo Ahorrado en Tienda", "48 horas / mes", "1.9 horas diarias en mostrador", C_NAVY)

    # Figura 4 del informe en gran tamaño a la izquierda
    add_box(s10, 0.55, 2.45, 7.35, 4.55, "Figura 4: Términos y Variables con Mayor Peso por Categoría")
    add_picture_fit(s10, DOCX_MEDIA / "image5.png", 0.68, 2.88, 7.10, 4.00, trim_white=True)

    # 3 tarjetas cuadradas a la derecha (Lenguaje claro para dueño/vendedor)
    add_feature_card(
        s10, 8.10, 2.45, 4.68, 1.42,
        "¿Cómo Decide el Modelo?",
        "Identifica palabras clave del cliente como “cuánto sale”, “stock”, “retenes”, “original bajaj” o “despacharon” en 1 segundo.",
        C_BLUE
    )
    add_feature_card(
        s10, 8.10, 4.01, 4.68, 1.42,
        "¿Qué SÍ Puede Hacer?",
        "Clasificar el 94.2% de mensajes, responder 24/7 con precios y stock reales de los 48 repuestos y filtrar publicidad.",
        C_MINT_DARK
    )
    add_feature_card(
        s10, 8.10, 5.58, 4.68, 1.42,
        "¿Qué NO Puede Hacer?",
        "No inventa precios ni aprueba transferencias sin validación; si su certeza es menor a 65%, transfiere el chat al vendedor.",
        C_BLUE_DARK
    )

    add_speaker_notes(s10, (
        "Expositor: Renzo Taypicahuana.\n"
        "Explicar el impacto económico en Soles y horas, la Figura 4 de importancia de variables y qué sí y qué no puede hacer el modelo."
    ))

    # ==========================================================================
    # SLIDE 11: ARQUITECTURA DEL INFORME E INTEGRACIÓN CON EL MVP
    # ==========================================================================
    s11 = prs.slides.add_slide(blank)
    add_header(s11, 11, "Bloque 6 · Arquitectura e Integración con el MVP", "10. Arquitectura de Integración y Estado de Implementación")

    # Izquierda arriba: Diagrama de arquitectura del informe (image6.png)
    add_box(s11, 0.55, 1.15, 5.75, 3.65, "Arquitectura del Ecosistema Integrado")
    add_picture_fit(s11, DOCX_MEDIA / "image6.png", 0.68, 1.56, 5.50, 3.12, trim_white=True)

    # Izquierda abajo: Contrato JSON compacto
    add_box(s11, 0.55, 4.92, 5.75, 2.08, "Contrato JSON del Endpoint POST /predict")
    j_box = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.73), Inches(5.34), Inches(5.38), Inches(1.52))
    j_box.fill.solid()
    j_box.fill.fore_color.rgb = C_NAVY
    j_box.line.fill.background()
    tf_j = j_box.text_frame
    tf_j.word_wrap = True
    tf_j.margin_left = Inches(0.12)
    tf_j.margin_top = Inches(0.08)
    pj = tf_j.paragraphs[0]
    rj = pj.add_run()
    rj.text = (
        "ENTRADA: {\"mensaje\": \"Tienes cilindro Torito Bajaj 4T?\", \"canal\": \"WHATSAPP\"}\n"
        "SALIDA : {\"intencion\": \"COTIZACION\", \"confianza\": 0.9642,\n"
        "          \"repuestos\": [{\"nombre\": \"Cilindro Torito 4T\", \"precio\": 185.0, \"stock\": 23}]}"
    )
    rj.font.name = "Consolas"
    rj.font.size = Pt(9.2)
    rj.font.color.rgb = RGBColor(167, 243, 208)
    set_es_lang(rj)

    # Derecha: Tabla de estado actual (APF3 vs PROY)
    add_box(s11, 6.50, 1.15, 6.28, 5.85, "Estado Actual en APF3 frente a Meta Final (PROY)")
    headers_st = ["Componente del Proyecto", "Operativo Hoy en APF3", "Alcance para Semana 17"]
    rows_st = [
        ["Microservicio ML FastAPI (/predict, /interactions)", "Desplegado en vivo en Render", "Monitoreo mensual de datos."],
        ["Bot WhatsApp (+51 937 395 986) + Stock SQL", "Conectado 24/7 a PostgreSQL", "Validación automática de vouchers."],
        ["Clasificador y Analítica con Gráficas BI (React)", "Integrado en panel administrador", "Exportación de reportes en Excel."],
        ["Interacción en tiempo real Admin y Cliente", "Notificaciones y stock en vivo", "Reserva temporal de stock (30 min)."],
        ["Confirmación contable de pagos Yape y Plin", "Flujo asistido con captura", "Conciliación automática completa."],
    ]
    tbl_st = s11.shapes.add_table(len(rows_st) + 1, 3, Inches(6.68), Inches(1.65), Inches(5.92), Inches(5.10))
    style_table(tbl_st.table, headers_st, rows_st, [2.32, 1.80, 1.80], font_size=10.0)

    add_speaker_notes(s11, (
        "Expositor: Renzo Taypicahuana.\n"
        "Mostrar el diagrama de arquitectura del informe, el contrato JSON del endpoint POST /predict y el estado de implementación."
    ))

    # ==========================================================================
    # SLIDE 12: NORMATIVA PERUANA Y GESTIÓN DE RIESGOS
    # ==========================================================================
    s12 = prs.slides.add_slide(blank)
    add_header(s12, 12, "Bloque 7 · Cumplimiento Normativo y Riesgos", "11. Matriz de Cumplimiento Legal y Control de Riesgos")

    headers_norm = ["Requisito de la Norma Peruana", "Control Aplicado en el Dataset y Modelo", "Evidencia Verificable en el Proyecto"]
    rows_norm = [
        ["Ley N.° 29733 — Protección de Datos Personales", "Anonimización irreversible de teléfonos y nombres antes del entrenamiento.", "Columna cliente_id_anonimo (UUID v4) en las 520 filas del CSV."],
        ["Ley N.° 29571 — Código de Defensa del Consumidor", "Precios y stock consultados en tiempo real desde PostgreSQL; umbral < 65% deriva a asesor.", "Consulta SQL en vivo en app/main.py y aviso de asistente automático."],
        ["R. S. N.° 182-2020/SUNAT — Comprobantes de Pago", "Validación del comprobante Yape o Plin antes de autorizar el despacho de almacén.", "Flujo de seguimiento de pedidos y emisión de boleta electrónica."],
    ]
    tbl_norm = s12.shapes.add_table(len(rows_norm) + 1, 3, Inches(0.55), Inches(1.20), Inches(12.23), Inches(2.68))
    style_table(tbl_norm.table, headers_norm, rows_norm, [3.40, 4.53, 4.30], font_size=10.2)

    headers_risk = ["ID", "Riesgo Técnico u Operativo Identificado", "Impacto", "Plan de Mitigación Implementado"]
    rows_risk = [
        ["R1", "Hibernación del servicio gratuito en Render o desconexión de WhatsApp.", "Alto", "Endpoint ligero GET /health activo y reconexión automática de sesión."],
        ["R2", "Ingreso de nuevas marcas o líneas de repuestos al almacén de Comas.", "Medio", "Reentrenamiento mensual en 15 segundos con train_pipeline.py."],
        ["R3", "Mensajes de una sola palabra ('1', 'yape', 'precio') con baja certeza.", "Medio", "Menú interactivo numerado (Opciones 1 a 4) más umbral de derivación."],
        ["R4", "Diferencia de stock entre ventas en mostrador físico y WhatsApp.", "Alto", "Lectura transaccional sobre la misma base Supabase PostgreSQL."],
    ]
    tbl_risk = s12.shapes.add_table(len(rows_risk) + 1, 4, Inches(0.55), Inches(4.12), Inches(12.23), Inches(2.78))
    style_table(tbl_risk.table, headers_risk, rows_risk, [0.70, 4.50, 1.15, 5.88], font_size=10.2)

    add_speaker_notes(s12, (
        "Expositor: Josué Gutierrez.\n"
        "Detallar la matriz normativa de 3 columnas y los 4 riesgos técnicos y operativos hacia la entrega final."
    ))

    # ==========================================================================
    # SLIDE 13: CONCLUSIONES Y TRAZABILIDAD (ESTILO CLÁSICO, ORDENADO Y CONCISO)
    # ==========================================================================
    s13 = prs.slides.add_slide(blank)
    add_header(s13, 13, "Bloque 7 · Conclusiones y Trazabilidad", "12. Conclusiones y Evolución Integral del Proyecto")

    # Fila 1: 4 Indicadores Clave en cajas blancas clásicas (da orden visual inmediato)
    add_metric(s13, 0.55, 1.15, 2.90, 1.12, "F1-Macro en Prueba", "0.9393", "Supera la meta de 0.85", C_BLUE)
    add_metric(s13, 3.66, 1.15, 2.90, 1.12, "Precisión en SPAM", "100%", "Cero clientes descartados", C_BLUE_DARK)
    add_metric(s13, 6.77, 1.15, 2.90, 1.12, "Tiempo de Respuesta", "1.31 s", "Atención automática 24/7", C_MINT_DARK)
    add_metric(s13, 9.88, 1.15, 2.90, 1.12, "Impacto Mensual", "S/ 2,250 a 2,850", "Ventas nocturnas recuperadas", C_BLUE)

    # Fila 2: 3 Tarjetas blancas clásicas con texto conciso y sin espacio vacío
    add_feature_card(
        s13, 0.55, 2.42, 3.92, 1.82,
        "1. Valor Generado Hoy",
        "Clasifica el 94.2% de consultas en vivo en el WhatsApp +51 937 395 986, cotiza con el stock real de PostgreSQL y ahorra 48 horas al mes en tienda.",
        C_BLUE
    )
    add_feature_card(
        s13, 4.70, 2.42, 3.92, 1.82,
        "2. Límites Reconocidos",
        "Entrenado con 520 consultas (25% reales y 75% simuladas) del catálogo Bajaj y TVS. Los casos ambiguos (5.8%) pasan al asesor si la certeza es menor a 65%.",
        C_BLUE_DARK
    )
    add_feature_card(
        s13, 8.85, 2.42, 3.93, 1.82,
        "3. Próximo Paso al Cierre",
        "Reentrenar el modelo con las nuevas conversaciones reales de las semanas 15 y 16, activar la reserva temporal de stock y medir el retorno final.",
        C_MINT_DARK
    )

    # Fila 3: Tabla clásica corporativa con el mismo estilo de toda la presentación
    headers_tr = ["Etapa del Proyecto", "Objetivo Comprometido", "Resultado Logrado y Verificable"]
    rows_tr = [
        ["APF1 · Diagnóstico", "Resolver la pérdida del 35% a 40% de consultas nocturnas.", "Meta definida: respuesta menor a 5 s y F1-Macro mayor o igual a 0.85."],
        ["APF2 · MVP Cloud", "Desplegar tienda web, base PostgreSQL y contrato de 12 campos.", "E-commerce React, API Spring Boot y catálogo real de 48 repuestos."],
        ["APF3 · Modelo ML", "Entrenar clasificador supervisado e integrarlo al flujo en vivo.", "SVM Lineal (F1 = 0.9393) activo en WhatsApp +51 937 395 986 y Bandeja BI."],
        ["PROY · Cierre Final", "Consolidar la conversión comercial nocturna y el monitoreo.", "Reserva automática de inventario y reporte ejecutivo de ventas."],
    ]
    tbl_tr = s13.shapes.add_table(len(rows_tr) + 1, 3, Inches(0.55), Inches(4.42), Inches(12.23), Inches(2.55))
    style_table(tbl_tr.table, headers_tr, rows_tr, [2.30, 4.80, 5.13], font_size=10.4)

    add_speaker_notes(s13, (
        "Expositor: Todo el equipo.\n"
        "Cerrar presentando los 4 indicadores clave, las 3 conclusiones puntuales y la tabla de evolución desde APF1 hasta el Proyecto Final."
    ))

    out_paths = [
        ROOT_DIR / "APF3_TD_Grupo01_ML_Innovacion_Final.pptx",
        ROOT_DIR / "APF3_TD_Grupo01_ML_Innovacion_Limpio.pptx",
        ROOT_DIR / "Entregables_APF3_AulaVirtual" / "APF3_TD_Grupo01_ML_Innovacion.pptx",
        ROOT_DIR / "Entregables_APF3_AulaVirtual" / "APF3_TD_Grupo_ML_Innovacion.pptx",
        ROOT_DIR / "APF3_TD_Grupo_ML_Innovacion.pptx",
        Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b\APF3_TD_Grupo_ML_Innovacion.pptx"),
    ]
    for p in out_paths:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(p))
            print(f"[OK] Presentación actualizada en: {p} ({p.stat().st_size / 1024:.1f} KB)")
        except PermissionError:
            print(f"[AVISO] {p.name} está abierto en PowerPoint; se guardó en las demás rutas.")


if __name__ == "__main__":
    build_presentation()
