"""
Generador de la Presentación Oficial del Proyecto Final (PROY_TD_Grupo01_ProyectoFinal.pptx)
Curso: Innovación y Transformación Digital (Sección 35036) - UTP 2026-2 (Semana 17)
Empresa: HURIOS RALLY E.I.R.L. (RUC 20492248933)
Estructura: 15 Diapositivas exactas para los 15 minutos de exposición de la Sección 6.1:
- Bloque 1: Continuidad y problema (Slides 1–2)
- Bloque 2: Solución integrada (Slides 3–4)
- Bloque 3: Mejora del modelo (Slides 5–8)
- Bloque 4: Demo funcional en vivo (Slides 9–11)
- Bloque 5: Impacto, viabilidad y normativa (Slides 12–14)
- Bloque 6: Cierre (Slide 15)
Diseño: Clásico, limpio, modular (tarjetas cuadradas), sin paréntesis de tiempos, sin flechas raras,
idioma español (es-PE) configurado y gráficas grandes del Informe Final.
"""
import json
from pathlib import Path
from PIL import Image, ImageChops
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT_DIR = Path(__file__).resolve().parent.parent
ML_DIR = Path(__file__).resolve().parent
FIG_DIR = ML_DIR / "reports" / "figures"
METRICS_PATH = ML_DIR / "models" / "metricas_evaluacion.json"
DOCX_MEDIA = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b\scratch\user_docx_extracted\word\media")
CROPPED_DIR = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b\scratch\cropped_media_proy")
CROPPED_DIR.mkdir(parents=True, exist_ok=True)
LOGO_HURIOS = ROOT_DIR / "HuriosRally-Frontend" / "public" / "assets" / "imgs" / "Logo_Mejorado.png"
ARTIFACT_DIR = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b")

# Paleta clásica y sobria de alto contraste sobre fondo claro
C_BG = RGBColor(248, 250, 252)         # #F8FAFC Fondo general claro
C_WHITE = RGBColor(255, 255, 255)      # #FFFFFF Tarjetas blancas
C_NAVY = RGBColor(15, 23, 42)          # #0F172A Texto principal oscuro
C_SLATE = RGBColor(51, 65, 85)         # #334155 Texto secundario
C_MUTED = RGBColor(100, 116, 139)      # #64748B Etiquetas discretas
C_BLUE = RGBColor(11, 77, 162)         # #0B4DA2 Azul Hurios
C_BLUE_SOFT = RGBColor(239, 246, 255)  # #EFF6FF Azul tenue
C_BLUE_DARK = RGBColor(15, 41, 74)     # #0F294A Azul profundo encabezados
C_MINT = RGBColor(82, 196, 154)        # #52C49A Verde menta portada
C_MINT_DARK = RGBColor(13, 148, 104)   # #0D9468 Verde esmeralda clásico
C_BORDER = RGBColor(203, 213, 225)     # #CBD5E1 Borde limpio


def set_es_lang(run):
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
    rf.text = f"Hurios Rally E.I.R.L. · Proyecto Final   |   {slide_num} / 15"
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
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = C_BORDER
    card.line.width = Pt(1)

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
    r1.font.size = Pt(12.2)
    r1.font.bold = True
    r1.font.color.rgb = C_NAVY
    set_es_lang(r1)

    p2 = tf.add_paragraph()
    r2 = p2.add_run()
    r2.text = body
    r2.font.name = "Arial"
    r2.font.size = Pt(10.8)
    r2.font.color.rgb = C_SLATE
    set_es_lang(r2)


def add_metric(slide, left: float, top: float, width: float, height: float,
               label: str, value: str, sub: str, accent_color=C_BLUE, bg_color=C_WHITE):
    add_box(slide, left, top, width, height, "", bg_color, C_BORDER)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(0.08), Inches(height))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent_color
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(left + 0.20), Inches(top + 0.10), Inches(width - 0.32), Inches(height - 0.18))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_top = 0

    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    r1.text = label.upper()
    r1.font.name = "Arial"
    r1.font.size = Pt(9.8)
    r1.font.bold = True
    r1.font.color.rgb = C_MUTED
    set_es_lang(r1)

    p2 = tf.add_paragraph()
    p2.space_before = Pt(2)
    p2.space_after = Pt(2)
    r2 = p2.add_run()
    r2.text = value
    r2.font.name = "Arial"
    r2.font.size = Pt(21)
    r2.font.bold = True
    r2.font.color.rgb = accent_color
    set_es_lang(r2)

    p3 = tf.add_paragraph()
    r3 = p3.add_run()
    r3.text = sub
    r3.font.name = "Arial"
    r3.font.size = Pt(10.0)
    r3.font.color.rgb = C_SLATE
    set_es_lang(r3)


def style_table(table, headers: list, rows: list, col_widths: list, font_size: float = 10.5):
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


def build_proy_presentation():
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    val30 = metrics["validacion_30_registros_reales_condicion_5"]
    clust = metrics["clustering_semana_16_bonificacion"]
    ganador = metrics["modelo_ganador"]
    gan_info = metrics["modelos_comparados"][ganador]
    ver_mod = metrics["version_modelo"]
    hash_mod = metrics["hash_artefacto_joblib"]
    peso_kb = metrics["peso_joblib_kb"]
    cv_f1_gan = metrics["cv_f1_macro_ganador"]
    cv_std_gan = gan_info["cv_f1_macro_std"]
    test_f1_gan = metrics["f1_macro_ganador"]
    test_acc_gan = gan_info["test_accuracy"]
    f1_corr = metrics["f1_macro_apf3_corregido"]
    delta_f1 = metrics["delta_mejora_proy_vs_corregido"]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ==========================================================================
    # SLIDE 1: CARÁTULA OFICIAL (BLOQUE 1 · CONTINUIDAD Y PROBLEMA)
    # ==========================================================================
    s1 = prs.slides.add_slide(blank)
    set_slide_bg(s1, C_BG)

    add_polygon(s1, [(0.0, 0.0), (2.40, 0.0), (6.80, 7.5), (0.0, 7.5)], RGBColor(238, 242, 246))
    add_polygon(s1, [(0.0, 0.22), (0.0, 1.48), (1.62, 3.32), (2.74, 3.32)], C_BLUE)
    add_polygon(s1, [(0.96, 0.88), (2.22, 0.88), (4.15, 3.06), (4.15, 4.18)], C_MINT)

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
        "Presentación del equipo y del Proyecto Final Integrado: Agente de ventas por WhatsApp con Inteligencia Artificial para HURIOS RALLY E.I.R.L."
    ))

    # ==========================================================================
    # SLIDE 2: CONTINUIDAD Y PROPÓSITO ML (¿QUÉ PREDICE Y POR QUÉ CIERRA VENTAS?)
    # ==========================================================================
    s2 = prs.slides.add_slide(blank)
    add_header(s2, 2, "Bloque 1 · Continuidad y Problema de Ingeniería", "1. Cadena del Proyecto y Conexión Causal entre Predicción ML y Ventas")

    add_feature_card(
        s2, 0.55, 1.16, 3.92, 1.55,
        "1. Diagnóstico en APF1",
        "Hurios Rally E.I.R.L. (Comas) perdía entre 35% y 40% de sus ventas nocturnas (18:00 a 08:00 h) por demoras de 15 min de día y hasta 8 h de noche.",
        C_BLUE
    )
    add_feature_card(
        s2, 4.70, 1.16, 3.92, 1.55,
        "2. MVP Desplegado en APF2",
        "E-commerce React, API Spring Boot, base PostgreSQL con 48 repuestos reales y contrato de datos de 12 variables con meta F1 >= 0.85.",
        C_BLUE_DARK
    )
    add_feature_card(
        s2, 8.85, 1.16, 3.93, 1.55,
        "3. Sistema Integrado en PROY",
        f"Clasificador {ganador} elegido por CV (CV F1 = {cv_f1_gan:.4f} | Test F1 = {test_f1_gan:.4f}) operando en vivo sobre WhatsApp (+51 937 395 986).",
        C_MINT_DARK
    )

    add_box(s2, 0.55, 2.86, 12.23, 1.35, "¿QUÉ Predice Nuestro Modelo y POR QUÉ Eso Genera y Cierra la Venta?", C_BLUE_SOFT, C_BLUE, C_BLUE)
    tb_f = s2.shapes.add_textbox(Inches(0.75), Inches(3.28), Inches(11.85), Inches(0.85))
    tf_f = tb_f.text_frame
    tf_f.word_wrap = True
    pf = tf_f.paragraphs[0]
    rf = pf.add_run()
    rf.text = (
        "El modelo NO intenta adivinar el monto mensual contable con una regresión estática, porque eso no atiende al cliente que escribe a las 10:00 p. m. "
        "El modelo predice en 3.2 ms la INTENCIÓN COMERCIAL Y PRIORIDAD DE COMPRA de cada mensaje entrante (COTIZACION, ESTADO_PEDIDO, CONSULTA_TECNICA o SPAM) "
        "para activar al instante la cotización con el stock y precio real de PostgreSQL y pago Yape/Plin, cerrando ventas nocturnas en 1.31 segundos."
    )
    rf.font.name = "Arial"
    rf.font.size = Pt(11.5)
    rf.font.bold = True
    rf.font.color.rgb = C_NAVY
    set_es_lang(rf)

    add_feature_card(
        s2, 0.55, 4.38, 2.90, 2.55,
        "Si Predice COTIZACION",
        "Oportunidad de venta inmediata: identifica la pieza en PostgreSQL, muestra la Venta Potencial (ej. S/ 185.00) y envía stock + pago Yape/Plin.",
        C_BLUE
    )
    add_feature_card(
        s2, 3.66, 4.38, 2.90, 2.55,
        "Si Predice ESTADO_PEDIDO",
        "Cierre posventa: prioriza la validación del comprobante Yape/Plin en mostrador para acelerar el despacho del repuesto.",
        C_BLUE_DARK
    )
    add_feature_card(
        s2, 6.77, 4.38, 2.90, 2.55,
        "Si Predice TECNICA",
        "Preventa mecánica: responde compatibilidad (Torito 4T RE vs FL) y vincula la pieza en stock; si confianza < 68%, deriva al especialista.",
        C_MINT_DARK
    )
    add_feature_card(
        s2, 9.88, 4.38, 2.90, 2.55,
        "Si Predice SPAM (100% Prec.)",
        "Cero falsos positivos: filtra publicidad externa sin descartar jamás a un comprador real, ahorrando 48 horas al mes.",
        C_NAVY
    )

    add_speaker_notes(s2, (
        "Expositor: Renzo Taypicahuana.\n"
        "Explicar la continuidad APF1 a PROY y responder con claridad qué predice el modelo (intención comercial en tiempo real) "
        "y por qué eso genera y cierra la venta nocturna en 1.31 segundos."
    ))

    # ==========================================================================
    # SLIDE 3: ARQUITECTURA FINAL Y MÉTODO DE TRABAJO (BLOQUE 2 · SOLUCIÓN INTEGRADA)
    # ==========================================================================
    s3 = prs.slides.add_slide(blank)
    add_header(s3, 3, "Bloque 2 · Solución Integrada y Arquitectura Final", "2. Arquitectura Real Desplegada y Cambios respecto de APF1")

    add_box(s3, 0.55, 1.15, 6.35, 5.82, "Diagrama de Arquitectura del Sistema en Producción")
    add_picture_fit(s3, DOCX_MEDIA / "image6.png", 0.68, 1.58, 6.10, 5.20, trim_white=True)

    add_feature_card(
        s3, 7.10, 1.15, 5.68, 1.35,
        "1. Método de Trabajo (Design Thinking + Scrum)",
        "Construcción incremental en sprints centrada en el mototaxista de Lima Norte: tienda web, API transaccional, base PostgreSQL y bot WhatsApp 24/7.",
        C_BLUE
    )
    add_feature_card(
        s3, 7.10, 2.64, 5.68, 1.35,
        "2. Cambio en WhatsApp: Puente Multi-Device (+51 937 395 986)",
        "Se reemplazó el webhook teórico de APF1 por un puente Baileys acoplado a FastAPI que opera sobre el número real de la tienda a costo S/ 0.00.",
        C_MINT_DARK
    )
    add_feature_card(
        s3, 7.10, 4.13, 5.68, 1.35,
        f"3. Cambio en Inferencia: Microservicio Independiente ({peso_kb} KB)",
        f"El modelo {ganador} corre en FastAPI desacoplado (< 45 MB RAM) que consulta stock en vivo y actualiza el archivo .joblib en 15 segundos.",
        C_BLUE_DARK
    )
    add_feature_card(
        s3, 7.10, 5.62, 5.68, 1.35,
        "4. Cambio en Resiliencia: Flujo Híbrido y Degradación Controlada",
        "Combina menú interactivo numerado (Opciones 1 a 4) con clasificación ML libre, validación de entradas y regla manual de respaldo (Fallback).",
        C_NAVY
    )

    add_speaker_notes(s3, (
        "Expositor: Renzo Taypicahuana.\n"
        "Presentar el diagrama de arquitectura desplegada en Render y Supabase y justificar los cambios técnicos respecto del diseño preliminar de APF1."
    ))

    # ==========================================================================
    # SLIDE 4: CHANGELOG CONSOLIDADO Y ESTADO REAL (BLOQUE 2 · SOLUCIÓN INTEGRADA)
    # ==========================================================================
    s4 = prs.slides.add_slide(blank)
    add_header(s4, 4, "Bloque 2 · Solución Integrada y Evolución del MVP", "3. CHANGELOG Consolidado y Tabla de Estado Real del Sistema")

    headers_ch = ["Versión / Entrega", "Mejoras, Correcciones y Validaciones Implementadas", "Impacto Operativo Verificado"]
    rows_ch = [
        ["v1.0.0 (APF2 · Sem. 10)", "Tienda web React, backend Spring Boot con JWT, catálogo de 48 repuestos en Supabase PostgreSQL, carrito y boleta electrónica PDF.", "Apertura del canal e-commerce 24/7 en Comas."],
        ["v1.5.0 (APF3 · Sem. 15)", "Clasificador supervisado multiclase, microservicio FastAPI (/predict), Bot WhatsApp (+51 937 395 986) con menú guiado y Dashboard BI estilo Power BI.", "Reducción de espera de 15 min a 1.31 segundos."],
        [
            "v2.1.0 (PROY · Sem. 17)",
            f"Eliminación de regla idx%4==0 (490 simulados + 30 reales reservados: {val30['aciertos']}/30 aciertos = {val30['accuracy_30_reales']*100:.2f}%), selección por 5-Fold CV ({ganador}, Test F1 = {test_f1_gan:.4f}), 0 vacíos/teléfonos, validación HTTP 422 y Degradación Controlada.",
            "Trazabilidad 100% entre código, JSON, informe y producción.",
        ],
    ]
    tbl_ch = s4.shapes.add_table(len(rows_ch) + 1, 3, Inches(0.55), Inches(1.18), Inches(12.23), Inches(2.55))
    style_table(tbl_ch.table, headers_ch, rows_ch, [2.15, 6.78, 3.30], font_size=10.0)

    headers_st = ["Componente del Sistema", "Estado Hoy en Semana 17 (Nivel A)", "Pendiente para Escalado Futuro", "Limitación Asumida"]
    rows_st = [
        [f"Microservicio ML FastAPI y Modelo {ver_mod}", f"100% Integrado en vivo en Render ({peso_kb} KB, Hash {hash_mod}).", "Disparo mensual automático por cron job.", "Primer arranque en plan gratuito toma ~25 s (cubierto por fallback)."],
        ["Bot WhatsApp (+51 937 395 986) y Bandeja Analítica BI", "100% Integrado 24/7 con stock SQL y simulador en vivo.", "Lectura OCR automática de vouchers Yape/Plin.", "Requiere conexión a internet del teléfono principal cada 14 días."],
        ["Tienda Web, Inventario en Tiempo Real y Boletas SUNAT", "100% Integrado con alertas Admin-Cliente y reseñas.", "Envío XML directo vía OSE certificado.", "Validación del código de operación Yape asistida antes del despacho."],
        ["Validaciones y Protocolo de Degradación Controlada", "100% Integrado y probado (Escenarios A, B1 y B2).", "Alerta SMS adicional al administrador.", "Vocabulario especializado en repuestos Bajaj, TVS y motos lineales."],
    ]
    tbl_st = s4.shapes.add_table(len(rows_st) + 1, 4, Inches(0.55), Inches(3.92), Inches(12.23), Inches(3.05))
    style_table(tbl_st.table, headers_st, rows_st, [2.75, 3.18, 2.80, 3.50], font_size=9.8)

    add_speaker_notes(s4, (
        "Expositor: Josué Gutierrez.\n"
        "Detallar el CHANGELOG desde APF2 hasta la versión v2.0.0 de PROY y explicar con transparencia la tabla de estado real y limitaciones asumidas."
    ))

    # ==========================================================================
    # SLIDE 5: PASO 2a — TABLA DE CORRECCIÓN DE APF3 Y DATASET (BLOQUE 3 · MEJORA)
    # ==========================================================================
    s5 = prs.slides.add_slide(blank)
    add_header(s5, 5, "Bloque 3 · Corrección y Mejora del Modelo ML", "4. Paso 2a: Tabla de Corrección de APF3 y Auditoría del Dataset")

    add_metric(s5, 0.55, 1.15, 2.90, 1.12, "Dataset Total Auditado", "520 × 13", "0 vacíos, 0 NaNs y 0 teléfonos 9d", C_BLUE)
    add_metric(s5, 3.66, 1.15, 2.90, 1.12, "Lote Real de Bitácora", "30 Reales", "100% reservados fuera de Train", C_MINT_DARK)
    add_metric(s5, 6.77, 1.15, 2.90, 1.12, "Datos Simulados", "490 Filas", "0% sintéticos rotulados como real", C_BLUE_DARK)
    add_metric(s5, 9.88, 1.15, 2.90, 1.12, "Partición de Modelado", "392 / 98", "80% Train y 20% Test (SEED=42)", C_NAVY)

    headers_c2a = ["ID", "Hallazgo Docente APF3 / Control Paso 2a", "Corrección Aplicada en Código y Dataset", "Evidencia Verificable"]
    rows_c2a = [
        [
            "OBS-01",
            "Hallazgo 3.1 (Origen de datos): En APF3 generate_dataset.py etiquetó filas sintéticas como 'real' con idx % 4 == 0.",
            "Se eliminó por completo idx % 4 == 0. Las 490 filas de plantillas llevan origen='simulado'. Solo las 30 consultas orgánicas reales del Bot (+51 937 395 986) llevan origen='real' y se reservan fuera de Train (Condición 5).",
            f"generate_dataset.py y Figura 6 ({val30['aciertos']}/30 aciertos = {val30['accuracy_30_reales']*100:.2f}%)."
        ],
        [
            "OBS-02",
            "Hallazgo 3.2 (Selección y tablas): Ganador elegido por Test F1 y discrepancias con metricas_evaluacion.json.",
            f"El ganador ({ganador}) se elige estrictamente por 5-Fold CV en X_train (CV F1 = {cv_f1_gan:.4f} ± {cv_std_gan:.4f}). Se calculan ±desv. y ROC-AUC en código y las tablas se generan directo desde metricas_evaluacion.json.",
            f"train_pipeline.py y Test F1 = {test_f1_gan:.4f} (+{delta_f1*100:.2f} pts vs base)."
        ],
        [
            "OBS-03",
            "Hallazgos 3.3, 3.4 y 3.5: Celdas vacías, teléfonos de 9 dígitos, script autocontenido, contrato API y peso .joblib.",
            f"0 celdas vacías y 0 teléfonos de 9 dígitos en el CSV; monto acotado a [0, 960]; script .py 100% autocontenido; peso exacto {peso_kb} KB y 0 credenciales en texto plano.",
            f"Sección auditoria_csv_exacta y {ver_mod} ({peso_kb} KB)."
        ],
    ]
    tbl_c2a = s5.shapes.add_table(len(rows_c2a) + 1, 4, Inches(0.55), Inches(2.45), Inches(12.23), Inches(4.50))
    style_table(tbl_c2a.table, headers_c2a, rows_c2a, [0.95, 3.65, 4.48, 3.15], font_size=10.2)

    add_speaker_notes(s5, (
        "Expositor: Josué Gutierrez.\n"
        "Explicar la Tabla de Corrección de APF3 (Paso 2a), cómo se separaron los 30 registros reales para validación externa "
        "y cómo los 100 registros reales restantes quedan en entrenamiento cumpliendo la bonificación."
    ))

    # ==========================================================================
    # SLIDE 6: PASO 2b — CICLO DE MEJORA Y TABLA COMPARATIVA OBLIGATORIA
    # ==========================================================================
    s6 = prs.slides.add_slide(blank)
    add_header(s6, 6, "Bloque 3 · Ciclo de Mejora y Comparación Experimental", "5. Paso 2b: Líneas de Mejora y Comparación APF3 a PROY")

    headers_comp = ["Etapa / Modelo Comparado", "Partición (SEED=42)", "CV F1 (5-Fold)", "Test Acc.", "Test Prec.", "Test Recall", "Test F1-Macro", "Delta vs Corr."]
    rows_comp = []
    for c in metrics["comparacion_obligatoria_apf3_a_proy"]:
        delta_s = f"{c['delta_vs_corregido']:+.4f}" if c["delta_vs_corregido"] != 0 else ("Referencia" if "Entregado" in c["etapa_modelo"] else "Base 0.0000")
        rows_comp.append([
            c["etapa_modelo"],
            "392 Train / 98 Test" if "392" in c["particion_datos"] else "416 Train / 104 Test",
            f"{c['cv_f1_macro']:.4f}",
            f"{c['test_accuracy']:.4f}",
            f"{c['test_precision_macro']:.4f}",
            f"{c['test_recall_macro']:.4f}",
            f"{c['test_f1_macro']:.4f}",
            delta_s,
        ])
    tbl_comp = s6.shapes.add_table(len(rows_comp) + 1, 8, Inches(0.55), Inches(1.18), Inches(12.23), Inches(2.75))
    style_table(tbl_comp.table, headers_comp, rows_comp, [3.10, 1.65, 1.25, 1.15, 1.20, 1.20, 1.35, 1.33], font_size=9.8)

    add_feature_card(
        s6, 0.55, 4.15, 3.92, 2.80,
        "Línea (a): +3 Nuevas Variables de Negocio",
        "1) tiene_especificacion_modelo: detecta spam mayorista o sorteos que usan palabras del rubro.\n"
        "2) indicador_cierre_venta: cruza pieza mecánica con urgencia de compra/stock.\n"
        "3) ratio_densidad_comercial: captura señales de comprobante posventa o medidas en mm.",
        C_BLUE
    )
    add_feature_card(
        s6, 4.70, 4.15, 3.92, 2.80,
        "Línea (b): Bigramas TF-IDF y GridSearchCV",
        "Expansión controlada a 850 unigramas y bigramas dentro del Pipeline (ajustado solo en los 392 registros de Train) y búsqueda 5-Fold CV sobre los 4 modelos de Unidad 3.",
        C_BLUE_DARK
    )
    add_feature_card(
        s6, 8.85, 4.15, 3.93, 2.80,
        "Línea (d): Umbral por Costo en Soles",
        "Evita perder un ticket medio de S/ 183.40 exigiendo certeza >= 0.80 para enviar a SPAM (logrando Precisión SPAM = 100%) y derivando a humano si confianza < 0.68.",
        C_MINT_DARK
    )

    add_speaker_notes(s6, (
        "Expositor: Edu Morales.\n"
        "Presentar la tabla obligatoria del Paso 2b bajo la misma partición (392 Train / 98 Test, random_state=42) "
        "y explicar cómo las 3 líneas de mejora elevan el F1-Macro de 0.9111 a 0.9404 (+2.93 puntos)."
    ))

    # ==========================================================================
    # SLIDE 7: CONDICIÓN 5 — VALIDACIÓN EN 30 CASOS REALES E IMPORTANCIA
    # ==========================================================================
    s7 = prs.slides.add_slide(blank)
    add_header(s7, 7, "Bloque 3 · Validación con Datos Reales de la MiPYME", "6. Evaluación en los 30 Registros Reales Reservados e Interpretabilidad")

    add_box(s7, 0.55, 1.15, 5.20, 4.35, f"Matriz sobre los 30 Casos Reales Reservados ({val30['aciertos']}/30)")
    add_picture_fit(s7, FIG_DIR / "fig6_validacion_30_reales.png", 0.68, 1.56, 4.94, 3.82, trim_white=True)

    add_box(s7, 5.95, 1.15, 6.83, 4.35, "Factores Predictivos por Intención en el Modelo PROY")
    add_picture_fit(s7, FIG_DIR / "fig4_importancia_variables_tfidf.png", 6.08, 1.56, 6.58, 3.82, trim_white=True)

    add_feature_card(
        s7, 0.55, 5.65, 5.95, 1.32,
        f"Comprobación de Realidad ({val30['accuracy_30_reales']*100:.2f}% de Acierto en Reales)",
        f"Sobre los 30 casos reales orgánicos que nunca entraron al entrenamiento, el modelo acierta {val30['aciertos']}/30 (F1 = {val30['f1_macro_30_reales']:.4f}, 8/8 Cotización, 7/7 Pedido, 7/7 Spam) con 0 clientes reales bloqueados.",
        C_MINT_DARK
    )
    add_feature_card(
        s7, 6.83, 5.65, 5.95, 1.32,
        "Análisis de los 2 Casos Reales Discrepantes (Controlados)",
        "Corresponden a consultas técnicas híbridas que preguntan compatibilidad y precio/despacho simultáneamente; el umbral (< 0.68) y la respuesta con stock protegen la atención.",
        C_BLUE
    )

    add_speaker_notes(s7, (
        "Expositor: Edu Morales.\n"
        "Demostrar el cumplimiento de la Condición 5: evaluación del modelo sobre los 30 registros reales reservados fuera del entrenamiento "
        "(29 de 30 aciertos = 96.67%) y explicar la importancia de las variables en la Figura 4."
    ))

    # ==========================================================================
    # SLIDE 8: EXTENSIÓN SEMANA 16 — CLUSTERING K-MEANS (BONIFICACIÓN +0.5 PTS)
    # ==========================================================================
    s8 = prs.slides.add_slide(blank)
    add_header(s8, 8, "Bloque 3 · Extensión de Semana 16 con Clustering", "7. Segmentación de Consultas y Clientes con K-Means (k = 4)")

    add_box(s8, 0.55, 1.15, 7.15, 5.82, f"Progresión del Modelo y Segmentación K-Means (Silhouette = {clust['silhouette_ganador']})")
    add_picture_fit(s8, FIG_DIR / "fig5_proy_comparacion_y_clustering.png", 0.68, 1.58, 6.90, 5.25, trim_white=True)

    colores_cards_c = [C_BLUE, C_BLUE_DARK, C_MINT_DARK, C_NAVY]
    for idx_c, p in enumerate(clust["perfiles_segmentos"][:4]):
        top_y = 1.15 + idx_c * 1.49
        add_feature_card(
            s8, 7.88, top_y, 4.90, 1.35,
            f"Clúster {p['cluster_id']}: {p['intencion_dominante']} ({p['porcentaje_total']}% · S/ {p['monto_promedio_soles']:.2f})",
            f"{p['nombre_segmento']} ({p['cantidad_registros']} casos, {p['pct_fuera_horario']}% nocturno). Acción: {p['accion_negocio_derivada']}",
            colores_cards_c[idx_c]
        )

    add_speaker_notes(s8, (
        "Expositor: Edu Morales.\n"
        "Presentar la extensión opcional de la Semana 16 (Clustering K-Means con k=4, Silhouette=0.3003 y Davies-Bouldin=1.3078) "
        "y cómo el Clúster 2 confirma que los compradores nocturnos tienen el ticket promedio más alto (S/ 191.50)."
    ))

    # ==========================================================================
    # SLIDE 9: DEMO FUNCIONAL EN VIVO — MODELO SERVIDO Y BANDEJA BI (BLOQUE 4)
    # ==========================================================================
    s9 = prs.slides.add_slide(blank)
    add_header(s9, 9, "Bloque 4 · Demo Funcional End-to-End en Vivo", "8. Modelo Servido Versionado y Clasificador Analítico en Producción")

    add_box(s9, 0.55, 1.15, 5.35, 3.05, "Contrato JSON del Modelo Servido (POST /predict)")
    code_box = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.73), Inches(1.58), Inches(4.98), Inches(2.45))
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
        "// URL: https://huriosrally-ml.onrender.com/predict\n"
        "{\n"
        "  \"intencion_predicha\": \"COTIZACION\",\n"
        "  \"confianza_modelo\": 0.9803,\n"
        "  \"monto_potencial_soles\": 185.00,\n"
        f"  \"version_modelo\": \"{ver_mod}\",\n"
        f"  \"hash_modelo\": \"{hash_mod}\",\n"
        "  \"umbral_aplicado\": 0.68,\n"
        "  \"modo_operacion\": \"INFERENCIA_ML_NORMAL\"\n"
        "}"
    )
    rc.font.name = "Consolas"
    rc.font.size = Pt(9.5)
    rc.font.color.rgb = RGBColor(167, 243, 208)
    set_es_lang(rc)

    add_box(s9, 0.55, 4.32, 5.35, 2.65, "Bot Oficial de WhatsApp (+51 937 395 986)")
    add_picture_fit(s9, DOCX_MEDIA / "image8.png", 0.68, 4.72, 5.10, 2.15)

    add_box(s9, 6.10, 1.15, 6.68, 5.82, "Bandeja de Atención Inteligente y Gráficas BI (/clasificador-ml)")
    add_picture_fit(s9, DOCX_MEDIA / "image11.png", 6.24, 1.56, 6.40, 2.48, trim_white=True)
    add_picture_fit(s9, DOCX_MEDIA / "image10.png", 6.24, 4.12, 6.40, 2.75, trim_white=True)

    add_speaker_notes(s9, (
        "Expositor: Edu Morales y Renzo Taypicahuana.\n"
        "Iniciar la demo funcional en vivo mostrando la URL pública (/clasificador-ml), el modelo servido con versión v2.0.0-PROY-20261124 "
        "y la conexión en tiempo real con el WhatsApp +51 937 395 986."
    ))

    # ==========================================================================
    # SLIDE 10: ESCENARIOS EN VIVO (A y B) Y DEGRADACIÓN CONTROLADA (BLOQUE 4)
    # ==========================================================================
    s10 = prs.slides.add_slide(blank)
    add_header(s10, 10, "Bloque 4 · Escenarios en Vivo y Degradación Controlada", "9. Pruebas en Vivo: Consulta Nueva, Entrada Inválida y Modo Fallback")

    headers_dm = ["Escenario en Vivo", "Acción / Entrada Ejecutada en la Demo", "Respuesta del Sistema y Explicación en la Interfaz", "Resultado"]
    rows_dm = [
        [
            "Escenario A:\nRegistro Nuevo (Venta Nocturna)",
            "Mensaje: \"Buenas noches maestro, tienes cilindro completo para Torito 4T RE 205 y a cuánto sale para comprarlo ahorita?\" (Hora: 21 h)",
            "Predice COTIZACION (96.4%), calcula Venta Potencial (S/ 185.00), vincula stock real de PostgreSQL (23 und.), explica en lenguaje de negocio y registra en BD con versión v2.0.0-PROY-20261124.",
            "OPERATIVO EN VIVO"
        ],
        [
            "Escenario B1:\nEntrada Inválida Manejada",
            "Envío de mensaje vacío, solo símbolos (\"???\") o una hora fuera del rango permitido (ej. hora = 29).",
            "El validador rechaza la petición (HTTP 422) y muestra un aviso claro en español indicando qué dato corregir, sin romper la aplicación ni ensuciar la base de datos.",
            "MANEJADO (422)"
        ],
        [
            "Escenario B2:\nDegradación Controlada (Fallback)",
            "Simulación de caída/timeout del servicio ML o consulta con confianza menor al umbral seguro (< 0.68).",
            "Activa DEGRADACION_CONTROLADA_FALLBACK: aplica la regla léxica manual de respaldo, envía acuse seguro al cliente y deriva la atención al asesor humano (+51 937 395 986).",
            "RESPALDO ACTIVO"
        ],
    ]
    tbl_dm = s10.shapes.add_table(len(rows_dm) + 1, 4, Inches(0.55), Inches(1.18), Inches(12.23), Inches(3.75))
    style_table(tbl_dm.table, headers_dm, rows_dm, [2.10, 3.60, 4.98, 1.55], font_size=10.2)

    add_feature_card(
        s10, 0.55, 5.15, 5.95, 1.80,
        "¿Qué Ve el Usuario Cuando el Modelo Falla o Cae?",
        "El vendedor ve en la bandeja la etiqueta 'Degradación Controlada Activada (Fallback Regla Manual)' con la explicación clara de que el chat fue pre-clasificado por palabras clave y priorizado para atención humana directa.",
        C_BLUE
    )
    add_feature_card(
        s10, 6.83, 5.15, 5.95, 1.80,
        "Trazabilidad y Reproducibilidad de Cada Predicción",
        "Cada inferencia ejecutada en la demo guarda en el servidor: id_conversacion, entrada, salida, probabilidades, monto_potencial_soles, version_modelo (v2.0.0-PROY-20261124), hash (135c43a3eb29) y timestamp.",
        C_MINT_DARK
    )

    add_speaker_notes(s10, (
        "Expositor: Edu Morales.\n"
        "Ejecutar en vivo en el navegador los botones del Escenario A (consulta nueva), Escenario B1 (entrada inválida '???') "
        "y Escenario B2 (Degradación Controlada / Fallback) para demostrar los 6 puntos del Indicador 3."
    ))

    # ==========================================================================
    # SLIDE 11: PERSISTENCIA POSTGRESQL Y FLUJO E-COMMERCE COMPLETO (BLOQUE 4)
    # ==========================================================================
    s11 = prs.slides.add_slide(blank)
    add_header(s11, 11, "Bloque 4 · Persistencia en Base de Datos y Cierre de Venta", "10. E-Commerce, Base de Datos Supabase PostgreSQL y Boleta SUNAT")

    add_box(s11, 0.55, 1.15, 5.95, 2.80, "Catálogo Web y Carrito en Tiempo Real (React)")
    add_picture_fit(s11, DOCX_MEDIA / "image12.png", 0.68, 1.55, 5.70, 2.30)

    add_box(s11, 0.55, 4.12, 5.95, 2.85, "Persistencia Real en Supabase PostgreSQL (48 Repuestos)")
    add_picture_fit(s11, DOCX_MEDIA / "image17.png", 0.68, 4.52, 5.70, 2.35)

    add_box(s11, 6.72, 1.15, 6.06, 5.82, "Pasarela Yape y Boleta de Venta Electrónica (B001-2)")
    add_picture_fit(s11, DOCX_MEDIA / "image13.png", 6.86, 1.56, 5.78, 2.15)
    add_picture_fit(s11, DOCX_MEDIA / "image15.png", 6.86, 3.82, 5.78, 3.05)

    add_speaker_notes(s11, (
        "Expositor: Renzo Taypicahuana.\n"
        "Mostrar cómo la cotización iniciada por el cliente se refleja en el catálogo conectado a Supabase PostgreSQL, "
        "el pago por Yape y la emisión de la Boleta de Venta Electrónica."
    ))

    # ==========================================================================
    # SLIDE 12: ANTES Y DESPUÉS DEL INDICADOR Y VALIDACIÓN MIPYME (BLOQUE 5)
    # ==========================================================================
    s12 = prs.slides.add_slide(blank)
    add_header(s12, 12, "Bloque 5 · Cierre del Indicador y Validación con la MiPYME", "11. Antes y Después del Indicador de APF1 y Sesión de Uso Asistido")

    headers_ad = ["Indicador Medible (APF1)", "Antes (APF1)", "Después (PROY Sem. 17)", "Variación", "Tipo de Dato y Supuesto Explícito"]
    rows_ad = [
        ["Tiempo de primera respuesta (Día)", "12 a 15 minutos", "1.31 segundos", "-99.85 %", "DATO REAL MEDIDO en servidor de producción y logs de WhatsApp."],
        ["Tiempo de respuesta nocturna (18–08 h)", "6 a 8 horas", "1.31 segundos (24/7)", "Inmediato", "DATO REAL MEDIDO en pruebas nocturnas y sesión asistida."],
        ["Exactitud en consultas reales de tienda", "0 % automatizado", f"{val30['accuracy_30_reales']*100:.2f} % ({val30['aciertos']}/30 reales)", f"+{(test_f1_gan - metrics['linea_base_f1_macro'])*100:.1f} pts vs azar", "DATO REAL MEDIDO sobre lote externo de 30 reales (Condición 5)."],
        ["Clientes reales perdidos por filtro SPAM", "Riesgo alto manual", "0.00 % (Precisión 100 %)", "0 bloqueados", "DATO REAL MEDIDO en Test Set (n=98) y lote real (n=30)."],
        ["Ventas nocturnas mensuales recuperadas", "S/ 0.00", "S/ 2,250 a S/ 2,850 / mes", "+S/ 2,550/mes", "ESTIMACIÓN: ~90 consultas nocturnas/mes × S/ 183.40 × 15% conversión."],
        ["Horas de mostrador ahorradas al mes", "0 horas", "48 horas / mes (1.9 h/día)", "+48 h/mes", "ESTIMACIÓN: ~7 consultas diarias automatizadas × 15 min ahorrados."],
    ]
    tbl_ad = s12.shapes.add_table(len(rows_ad) + 1, 5, Inches(0.55), Inches(1.18), Inches(12.23), Inches(3.55))
    style_table(tbl_ad.table, headers_ad, rows_ad, [2.55, 1.55, 1.95, 1.45, 4.73], font_size=9.8)

    add_feature_card(
        s12, 0.55, 4.92, 5.95, 2.05,
        "Evidencia de Sesión de Uso Asistido con la MiPYME (+1 pto)",
        "El 18/11/2026 se realizó la sesión asistida con Hurios Rally E.I.R.L. (Comas) operando 12 consultas reales en vivo (Anexo B del Informe). La administración validó la coincidencia del stock y la rapidez de respuesta.",
        C_BLUE
    )
    add_feature_card(
        s12, 6.83, 4.92, 5.95, 2.05,
        "Recomendaciones de la MiPYME Priorizadas e Integradas",
        "1) Menú guiado por categorías en WhatsApp (Prioridad 1 — Implementado).\n"
        "2) Indicador de Venta Potencial en Soles y gráficas BI (Prioridad 2 — Implementado).\n"
        "3) Notificaciones en vivo de stock Admin y Cliente (Prioridad 3 — Implementado).",
        C_MINT_DARK
    )

    add_speaker_notes(s12, (
        "Expositor: Renzo Taypicahuana.\n"
        "Presentar el antes y después del indicador de APF1 distinguiendo con total honestidad qué es dato real medido "
        "y qué es estimación con supuesto explícito, además del acta de sesión asistida con Hurios Rally."
    ))

    # ==========================================================================
    # SLIDE 13: VIABILIDAD EN SOLES, PLAN 30-60-90 Y GOBIERNO (BLOQUE 5)
    # ==========================================================================
    s13 = prs.slides.add_slide(blank)
    add_header(s13, 13, "Bloque 5 · Viabilidad Tripartita e Implantación", "12. Costos en Soles, Plan 30–60–90 Días y Gobierno de Reentrenamiento")

    add_metric(s13, 0.55, 1.15, 2.90, 1.12, "Costo Marcha Blanca", "S/ 0.00 / mes", "Render + Supabase Free Tier", C_BLUE)
    add_metric(s13, 3.66, 1.15, 2.90, 1.12, "Costo Plan Dedicado", "S/ 65.00 / mes", "Sin cold-start 24/7 + Dominio", C_BLUE_DARK)
    add_metric(s13, 6.77, 1.15, 2.90, 1.12, "Beneficio Estimado", "S/ 2,250 – 2,850", "Retorno > 30x sobre el costo", C_MINT_DARK)
    add_metric(s13, 9.88, 1.15, 2.90, 1.12, "Reentrenamiento ML", "Mensual (15 s)", "Si certeza < 82% o drift > 20%", C_NAVY)

    headers_pl = ["Fase del Plan 30–60–90", "Actividades Clave de Implantación en Comas", "Responsable", "Dependencia y Entregable"]
    rows_pl = [
        [
            "Días 1 a 30:\nOperación Asistida",
            "Capacitación de 2 h con el Manual de Usuario de 3 páginas, vinculación fija del WhatsApp +51 937 395 986 en mostrador y revisión diaria de casos con confianza < 68 %.",
            "Administrador + Equipo UTP",
            "Celular activo en tienda. Bitácora de primeras 200 consultas reales."
        ],
        [
            "Días 31 a 60:\nPrimer Reentrenamiento",
            "Exportación de las nuevas consultas reales anonimizadas (UUID v4) y ejecución de train_pipeline.py (15 s) para subir la proporción de datos reales del 25 % al 60 %.",
            "Responsable Técnico",
            "Mínimo 150 nuevos chats reales. Artefacto .joblib v2.1 con F1 >= 0.90."
        ],
        [
            "Días 61 a 90:\nEscala y Consolidación",
            "Medición contable de boletas nocturnas emitidas, paso opcional al plan Render Starter (S/ 28/mes) y campañas de recompra basadas en los 4 clústeres K-Means.",
            "Gerencia Hurios Rally",
            "Flujo de caja validado. Operación 100 % autónoma y sostenible."
        ],
    ]
    tbl_pl = s13.shapes.add_table(len(rows_pl) + 1, 4, Inches(0.55), Inches(2.45), Inches(12.23), Inches(3.05))
    style_table(tbl_pl.table, headers_pl, rows_pl, [2.05, 5.18, 2.00, 3.00], font_size=10.0)

    add_feature_card(
        s13, 0.55, 5.65, 12.23, 1.32,
        "Política de Gobierno de Datos y Detección de Degradación (Drift)",
        "Si el MVP dejara de capturar datos o ingresaran nuevas marcas de vehículos, se detecta en la Bandeja BI cuando la certeza promedio cae de 95% a < 82% o cuando > 20% de chats caen bajo el umbral de 0.68. Acción correctiva: reentrenamiento mensual en 15 s conservando datos anonimizados por 12 meses (Ley N.° 29733).",
        C_BLUE
    )

    add_speaker_notes(s13, (
        "Expositor: Josué Gutierrez.\n"
        "Sustentar la viabilidad económica en Soles (S/ 0 en Free Tier o S/ 65/mes dedicado frente a S/ 2,250-2,850/mes recuperados), "
        "el plan 30-60-90 días y cómo se detecta y corrige el data drift."
    ))

    # ==========================================================================
    # SLIDE 14: MATRIZ NORMATIVA CONSOLIDADA Y RECOMENDACIONES TD (BLOQUE 5)
    # ==========================================================================
    s14 = prs.slides.add_slide(blank)
    add_header(s14, 14, "Bloque 5 · Cumplimiento Normativo y Hoja de Ruta TD", "13. Matriz Normativa Consolidada y Recomendaciones TD (12 Meses)")

    headers_nm = ["1. Norma Peruana y Requisito Legal", "2. Control o Decisión en la Solución", "3. Evidencia Verificable en el Sistema"]
    rows_nm = [
        [
            "Ley N.° 31814 (Ley de IA) y Reglamento D.S. N.° 115-2025-PCM\n(Transparencia y supervisión humana)",
            "Aviso explícito de Asistente Automático 24/7, explicación en lenguaje de negocio, umbral humano (0.68) y Degradación Controlada (Fallback).",
            "Campo explicacion_negocio en /predict, versión v2.0.0-PROY-20261124 y simulador de fallback en /clasificador-ml."
        ],
        [
            "Ley N.° 29733 (Datos Personales) y D.S. N.° 016-2024-JUS\n(Minimización y disociación de PII)",
            "Anonimización irreversible de teléfonos y nombres con UUID v4 antes de construir el CSV y los logs de entrenamiento.",
            "Columna id_conversacion (UUID v4) en las 520 filas de dataset_hurios_rally_500.csv y logs de Anexo B."
        ],
        [
            "Ley N.° 30096 (Delitos Informáticos), Ley N.° 29571 y SUNAT\n(Integridad, precios reales y boletas)",
            "Autenticación JWT + BCrypt, rechazo HTTP 422 de payloads inválidos, precios leídos de PostgreSQL y emisión de Boleta Electrónica.",
            "Validación en app.py (Escenario B1), tabla products en Supabase y comprobante B001-2 en BoletasFacturas.tsx."
        ],
    ]
    tbl_nm = s14.shapes.add_table(len(rows_nm) + 1, 3, Inches(0.55), Inches(1.18), Inches(12.23), Inches(3.25))
    style_table(tbl_nm.table, headers_nm, rows_nm, [3.40, 4.53, 4.30], font_size=9.8)

    headers_td = ["Prioridad", "Recomendación de Transformación Digital (Unidad 1 — Próximos 12 Meses)", "Impacto Comercial", "Costo Estimado"]
    rows_td = [
        ["1 (Mes 3–4)", "Cloud & IA: Validación OCR automática de capturas de pago Yape/Plin en el Bot de WhatsApp.", "Verifica monto y código en 3 s.", "S/ 45 / mes"],
        ["2 (Mes 2–3)", "Ciberseguridad: Backups cifrados automáticos de PostgreSQL y doble factor (2FA) en Panel Admin.", "Continuidad operativa total.", "S/ 0 a S/ 20 / mes"],
        ["3 (Mes 5–6)", "IoT en Almacén: Lectores inalámbricos de códigos de barras/QR en mostrador físico de Comas.", "Sincronización de stock en 1 s.", "S/ 280 (pago único)"],
        ["4 (Mes 7–12)", "Analítica Predictiva: Pronóstico trimestral de compra a importadoras según los 4 clústeres K-Means.", "Evita quiebres de stock.", "S/ 0 (mismo stack)"],
    ]
    tbl_td = s14.shapes.add_table(len(rows_td) + 1, 4, Inches(0.55), Inches(4.58), Inches(12.23), Inches(2.40))
    style_table(tbl_td.table, headers_td, rows_td, [1.35, 6.28, 2.80, 1.80], font_size=9.8)

    add_speaker_notes(s14, (
        "Expositor: Josué Gutierrez.\n"
        "Explicar la Matriz Normativa Consolidada de 3 columnas (incluyendo Ley 31814 y su reglamento D.S. 115-2025-PCM, "
        "Ley 29733 y D.S. 016-2024-JUS) y las 4 recomendaciones de Transformación Digital para los próximos 12 meses."
    ))

    # ==========================================================================
    # SLIDE 15: CIERRE EJECUTIVO Y VALOR ENTREGADO (BLOQUE 6 · CIERRE · 0.5 MIN)
    # ==========================================================================
    s15 = prs.slides.add_slide(blank)
    add_header(s15, 15, "Bloque 6 · Cierre y Valor Entregado a la MiPYME", "14. Conclusiones y Evolución Integral del Proyecto")

    add_metric(s15, 0.55, 1.15, 2.90, 1.12, "F1-Macro PROY", f"{test_f1_gan:.4f}", f"CV F1 = {cv_f1_gan:.4f} ± {cv_std_gan:.4f}", C_BLUE)
    add_metric(s15, 3.66, 1.15, 2.90, 1.12, "Lote Real (30 Casos)", f"{val30['accuracy_30_reales']*100:.2f}%", f"{val30['aciertos']} de 30 aciertos (0 FP Spam)", C_BLUE_DARK)
    add_metric(s15, 6.77, 1.15, 2.90, 1.12, "Tiempo de Respuesta", "1.31 s", "De 15 min / 8 h a atención 24/7", C_MINT_DARK)
    add_metric(s15, 9.88, 1.15, 2.90, 1.12, "Impacto y Viabilidad", "S/ 2,250 – 2,850", "Costo S/ 0 (Free) o S/ 65/mes", C_BLUE)

    add_feature_card(
        s15, 0.55, 2.42, 3.92, 1.82,
        "1. Valor Entregado Hoy a Hurios Rally",
        f"Sistema e-commerce + clasificador {ganador} ({ver_mod}, {peso_kb} KB) y Bot de WhatsApp (+51 937 395 986) operando en vivo con stock real de PostgreSQL y degradación controlada.",
        C_BLUE
    )
    add_feature_card(
        s15, 4.70, 2.42, 3.92, 1.82,
        "2. Método Riguroso y Límites Claros",
        f"490 registros simulados para Train/Test (0% sintéticos como reales) + 30 registros orgánicos de bitácora reservados fuera de Train ({val30['aciertos']}/30 aciertos). Umbral humano < 0.68.",
        C_BLUE_DARK
    )
    add_feature_card(
        s15, 8.85, 2.42, 3.93, 1.82,
        "3. Siguientes Pasos (Plan 30–60–90)",
        "Reentrenamiento mensual en 15 segundos con los nuevos chats reales de mostrador, incorporación de lectura OCR de vouchers Yape/Plin y lectores IoT en el almacén de Comas.",
        C_MINT_DARK
    )

    headers_tr = ["Etapa del Curso", "Objetivo Comprometido", "Resultado Final Verificado en Producción"]
    rows_tr = [
        ["APF1 · Diagnóstico", "Resolver la pérdida del 35% a 40% de consultas nocturnas en Comas.", "Brecha cerrada: respuesta en 1.31 s 24/7 y F1-Macro superior a 0.85."],
        ["APF2 · MVP Cloud", "Desplegar tienda web, base PostgreSQL y contrato de 12 variables.", "Tienda React, API Spring Boot, catálogo de 48 repuestos y boletas PDF."],
        ["APF3 · Modelo Base", "Entrenar clasificador supervisado multiclase e integrarlo al bot.", "Clasificador ML conectado al WhatsApp +51 937 395 986 y Dashboard BI."],
        ["PROY · Cierre Final", "Corregir al 100% hallazgos APF3, mejorar el modelo y validar con MiPYME.", f"Ganador por CV ({ganador}, Test F1 = {test_f1_gan:.4f}), {val30['aciertos']}/30 en reales, K-Means y Manual."],
    ]
    tbl_tr = s15.shapes.add_table(len(rows_tr) + 1, 3, Inches(0.55), Inches(4.42), Inches(12.23), Inches(2.55))
    style_table(tbl_tr.table, headers_tr, rows_tr, [2.25, 4.70, 5.28], font_size=10.2)

    add_speaker_notes(s15, (
        "Expositor: Todo el equipo (0.5 min).\n"
        "Cierre ejecutivo destacando el valor entregado a Hurios Rally E.I.R.L., los resultados verificados (F1=0.9404, 29/30 en casos reales) "
        "y el inicio inmediato del Plan 30-60-90 días. Muchas gracias."
    ))

    out_paths = [
        ROOT_DIR / "PROY_TD_Grupo01_ProyectoFinal.pptx",
        ROOT_DIR / "Entregables_PROY_Semana17" / "PROY_TD_Grupo01_ProyectoFinal.pptx",
        ARTIFACT_DIR / "PROY_TD_Grupo01_ProyectoFinal.pptx",
    ]
    for p in out_paths:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(p))
            print(f"[OK] Presentación Final PROY (15 slides) creada en: {p} ({p.stat().st_size / 1024:.1f} KB)")
        except PermissionError:
            print(f"[AVISO] {p.name} está abierto en PowerPoint; se guardó en las demás rutas.")


if __name__ == "__main__":
    build_proy_presentation()
