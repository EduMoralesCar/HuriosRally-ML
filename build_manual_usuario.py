"""
Generador del Manual de Usuario para la MiPYME (PROY_TD_Grupo01_ManualUsuario.docx)
Extensión: Máximo 3 páginas (Sección 5 de la Consigna PROY - Semana 17)
Contenido obligatorio:
1. Para qué sirve el sistema y cómo impulsa las ventas en Hurios Rally E.I.R.L.
2. Cómo usarlo en la operación diaria (WhatsApp +51 937 395 986, Bandeja ML y Tienda Web).
3. Qué significa cada resultado del modelo de Machine Learning (categorías, confianza y venta potencial).
4. Qué hacer si el modelo falla o activa la Degradación Controlada (protocolo de respaldo).
"""
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b\scratch\user_docx_extracted")
BUILD_DIR = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b\scratch\proy_manual_build")
ARTIFACT_DIR = Path(r"C:\Users\edomo\.gemini\antigravity\brain\c64fda5b-f49f-45f0-8fef-800658a6ac4b")


def esc(text: str) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def pack_docx(src_folder: Path, dest_docx: Path) -> None:
    dest_docx.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_docx, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in src_folder.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(src_folder).as_posix()
                zf.write(file_path, arcname)


def build_manual():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    shutil.copytree(TEMPLATE_DIR, BUILD_DIR)

    # Extraer sectPr del documento plantilla para mantener márgenes, encabezado y pie de página UTP
    orig_xml = (TEMPLATE_DIR / "word" / "document.xml").read_text(encoding="utf-8")
    sect_start = orig_xml.rfind("<w:sectPr")
    sect_end = orig_xml.rfind("</w:sectPr>") + len("</w:sectPr>")
    sect_pr_xml = orig_xml[sect_start:sect_end]

    # Mapear imágenes de word/media para insertar 2 capturas compactas del sistema real
    media_dir = BUILD_DIR / "word" / "media"
    rels_path = BUILD_DIR / "word" / "_rels" / "document.xml.rels"
    rels_tree = ET.parse(rels_path)
    rels_root = rels_tree.getroot()
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"

    # Registrar rIdManual1 (Bandeja BI image9.png) y rIdManual2 (Bot WhatsApp image8.png)
    for rid, fname in [("rIdManual1", "image9.png"), ("rIdManual2", "image8.png")]:
        el = ET.SubElement(rels_root, f"{{{rel_ns}}}Relationship")
        el.set("Id", rid)
        el.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
        el.set("Target", f"media/{fname}")
    rels_tree.write(rels_path, encoding="utf-8", xml_declaration=True)

    lines = []
    doc_pr_id = 7000

    def add_title_banner():
        lines.append(
            '<w:p><w:pPr><w:spacing w:before="40" w:after="60" w:line="260" w:lineRule="auto" /><w:jc w:val="center" /></w:pPr>'
            '<w:r><w:rPr><w:b /><w:bCs /><w:color w:val="0B4DA2" /><w:sz w:val="28" /><w:szCs w:val="28" /></w:rPr>'
            '<w:t>MANUAL DE USUARIO Y OPERACIÓN DIARIA PARA LA MIPYME</w:t></w:r></w:p>'
        )
        lines.append(
            '<w:p><w:pPr><w:spacing w:before="0" w:after="100" w:line="240" w:lineRule="auto" /><w:jc w:val="center" /></w:pPr>'
            '<w:r><w:rPr><w:b /><w:bCs /><w:color w:val="0F172A" /><w:sz w:val="22" /><w:szCs w:val="22" /></w:rPr>'
            '<w:t>HURIOS RALLY E.I.R.L. (RUC 20492248933 — Av. 22 de Agosto 1012, Comas, Lima)</w:t></w:r></w:p>'
        )

    def add_h1(num_title: str):
        lines.append(
            f'<w:p><w:pPr><w:spacing w:before="140" w:after="60" w:line="260" w:lineRule="auto" />'
            f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="0B4DA2" /></w:pBdr></w:pPr>'
            f'<w:r><w:rPr><w:b /><w:bCs /><w:color w:val="0B4DA2" /><w:sz w:val="22" /><w:szCs w:val="22" /></w:rPr>'
            f'<w:t>{esc(num_title)}</w:t></w:r></w:p>'
        )

    def add_p(text: str, bold_prefix: str = ""):
        runs = ""
        if bold_prefix:
            runs += (
                f'<w:r><w:rPr><w:b /><w:bCs /><w:sz w:val="19" /><w:szCs w:val="19" /></w:rPr>'
                f'<w:t xml:space="preserve">{esc(bold_prefix)}</w:t></w:r>'
            )
        runs += (
            f'<w:r><w:rPr><w:sz w:val="19" /><w:szCs w:val="19" /></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'
        )
        lines.append(
            f'<w:p><w:pPr><w:spacing w:before="30" w:after="50" w:line="250" w:lineRule="auto" /><w:jc w:val="both" /></w:pPr>{runs}</w:p>'
        )

    def add_bullet(bold_prefix: str, text: str):
        add_p(text, f"• {bold_prefix}")

    def add_table(headers: list[str], rows: list[list[str]], col_widths: list[int]):
        total_w = sum(col_widths)
        lines.append(
            f'<w:tbl><w:tblPr><w:tblStyle w:val="Tablaconcuadrcula2-nfasis1" />'
            f'<w:tblW w:w="{total_w}" w:type="dxa" />'
            f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1" /></w:tblPr><w:tblGrid>'
        )
        for cw in col_widths:
            lines.append(f'<w:gridCol w:w="{cw}" />')
        lines.append("</w:tblGrid>")

        # Encabezado
        lines.append(
            '<w:tr><w:trPr><w:cnfStyle w:val="100000000000" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:oddVBand="0" w:evenVBand="0" w:oddHBand="0" w:evenHBand="0" w:firstRowFirstColumn="0" w:firstRowLastColumn="0" w:lastRowFirstColumn="0" w:lastRowLastColumn="0" /></w:trPr>'
        )
        for c, h_text in enumerate(headers):
            cw = col_widths[c]
            lines.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{cw}" w:type="dxa" /><w:shd w:val="clear" w:color="auto" w:fill="0F294A" /></w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="230" w:lineRule="auto" /><w:jc w:val="left" /></w:pPr>'
                f'<w:r><w:rPr><w:b /><w:bCs /><w:color w:val="FFFFFF" /><w:sz w:val="18" /><w:szCs w:val="18" /></w:rPr>'
                f'<w:t xml:space="preserve">{esc(h_text)}</w:t></w:r></w:p></w:tc>'
            )
        lines.append("</w:tr>")

        for r_idx, row in enumerate(rows):
            bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
            lines.append("<w:tr>")
            for c, val in enumerate(row):
                cw = col_widths[c]
                bold_tag = "<w:b /><w:bCs />" if c == 0 else ""
                lines.append(
                    f'<w:tc><w:tcPr><w:tcW w:w="{cw}" w:type="dxa" /><w:shd w:val="clear" w:color="auto" w:fill="{bg}" /></w:tcPr>'
                    f'<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="230" w:lineRule="auto" /><w:jc w:val="left" /></w:pPr>'
                    f'<w:r><w:rPr>{bold_tag}<w:color w:val="0F172A" /><w:sz w:val="18" /><w:szCs w:val="18" /></w:rPr>'
                    f'<w:t xml:space="preserve">{esc(val)}</w:t></w:r></w:p></w:tc>'
                )
            lines.append("</w:tr>")
        lines.append("</w:tbl>")

    def add_image_compact(rid: str, fname: str, caption: str, max_w_emu: int = 4300000, max_h_emu: int = 2150000):
        nonlocal doc_pr_id
        img_path = media_dir / fname
        if not img_path.exists():
            return
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        cx = max_w_emu
        cy = int(cx * h_px / float(w_px))
        if cy > max_h_emu:
            cy = max_h_emu
            cx = int(cy * w_px / float(h_px))
        doc_pr_id += 1
        lines.append(
            f'<w:p><w:pPr><w:spacing w:before="40" w:after="20" w:line="230" w:lineRule="auto" /><w:jc w:val="center" /></w:pPr>'
            f'<w:r><w:rPr><w:noProof /></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
            f'<wp:extent cx="{cx}" cy="{cy}" /><wp:effectExtent l="0" t="0" r="0" b="0" />'
            f'<wp:docPr id="{doc_pr_id}" name="Picture {doc_pr_id}" />'
            f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1" /></wp:cNvGraphicFramePr>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{doc_pr_id}" name="Picture {doc_pr_id}" /><pic:cNvPicPr /></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" /><a:stretch><a:fillRect /></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0" /><a:ext cx="{cx}" cy="{cy}" /></a:xfrm><a:prstGeom prst="rect"><a:avLst /></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
        )
        lines.append(
            f'<w:p><w:pPr><w:spacing w:before="0" w:after="50" w:line="220" w:lineRule="auto" /><w:jc w:val="center" /></w:pPr>'
            f'<w:r><w:rPr><w:b /><w:bCs /><w:color w:val="334155" /><w:sz w:val="17" /><w:szCs w:val="17" /></w:rPr>'
            f'<w:t>{esc(caption)}</w:t></w:r></w:p>'
        )

    # =========================================================================
    # CONTENIDO DEL MANUAL DE USUARIO (DISEÑADO PARA CABER EN 3 PÁGINAS EXACTAS)
    # =========================================================================
    add_title_banner()

    add_h1("1. ¿Para qué sirve el sistema y cómo genera ventas en Hurios Rally E.I.R.L.?")
    add_p(
        "El Sistema Web E-Commerce y Agente Inteligente de Ventas por WhatsApp de HURIOS RALLY E.I.R.L. "
        "tiene como objetivo atender las 24 horas del día a los mototaxistas (Bajaj Torito 4T RE 205, FL, TVS King 200) "
        "y talleres mecánicos de Lima Norte, eliminando la pérdida del 35 % al 40 % de consultas nocturnas (18:00 a 08:00 h) "
        "y reduciendo el tiempo de primera respuesta de 15 minutos a 1.31 segundos."
    )
    add_table(
        ["Recurso en Producción", "Enlace / Número Oficial", "Acceso y Uso Operativo"],
        [
            ["Tienda Web y Panel Admin", "https://huriosrally-frontend.onrender.com", "Acceso público a catálogo; panel admin con credenciales institucionales."],
            ["Clasificador y Bandeja IA", "https://huriosrally-frontend.onrender.com/clasificador-ml", "Acceso directo en vivo a monitoreo WhatsApp, gráficas BI y simulador."],
            ["Bot Oficial de WhatsApp", "+51 937 395 986", "Atención automática 24/7 con menú guiado (1 al 4) y texto libre."],
            ["API ML / Swagger Backend", "https://huriosrally-ml.onrender.com/docs", "Modelo servido v2.1.0-PROY-20261124 (SVM Lineal elegido por 5-Fold CV)."],
        ],
        [2400, 3600, 3200],
    )

    add_h1("2. ¿Cómo usar el sistema en la operación diaria de la tienda?")
    add_bullet(
        "Paso 1 — Vinculación matutina del Bot de WhatsApp (+51 937 395 986): ",
        "Ingrese a /clasificador-ml y verifique que el indicador superior diga 'Bot Activo (+51 937 395 986)'. Si se reinició la sesión, haga clic en 'Vincular WhatsApp' y escanee el código QR o ingrese el código numérico de 8 dígitos desde el celular de la tienda.",
    )
    add_bullet(
        "Paso 2 — Atención automática por WhatsApp (Menú Guiado + Inteligencia Artificial): ",
        "Cuando un cliente escribe al +51 937 395 986, el robot ofrece 4 opciones rápidas (1: Cotizar repuestos por categoría y pagar con Yape/Plin/Tarjeta; 2: Consultas técnicas frecuentes; 3: Estado de pedido por DNI/Nombre; 4: Comunicarse con un asesor). Si el cliente escribe una frase libre (ej. 'Buenas noches maestro, tienes cilindro para Torito 4T y cuánto sale?'), el modelo ML clasifica la intención en 3.2 ms y responde con el precio y stock real desde Supabase PostgreSQL.",
    )
    add_bullet(
        "Paso 3 — Supervisión en la Bandeja de Atención Inteligente y Dashboard BI: ",
        "En la pantalla /clasificador-ml el administrador visualiza los 4 contadores superiores (Cotizaciones, Consultas Técnicas, Estado de Pedido y No Deseado). Al hacer clic en cualquier barra o tarjeta se filtra la bandeja izquierda; al seleccionar una conversación se muestra a la derecha la respuesta enviada, la venta potencial en Soles y los repuestos en stock.",
    )
    add_bullet(
        "Paso 4 — Confirmación de pagos Yape/Plin y actualización de inventario: ",
        "Las conversaciones clasificadas como 'Estado de pedido' o 'Solicitó asesor' deben atenderse con prioridad en mostrador verificando la captura de transferencia Yape/Plin y emitiendo la Boleta Electrónica en la pestaña 'Boletas y Facturas'. Cualquier cambio de stock en '/inventario' notifica en tiempo real a los clientes conectados.",
    )

    add_image_compact(
        "rIdManual1",
        "image9.png",
        "Figura 1. Vista operativa del Clasificador de Consultas, Gráficas BI y Bandeja de Clientes en Vivo.",
    )

    add_h1("3. ¿Qué significa cada resultado del Modelo de Machine Learning?")
    add_p(
        "El modelo clasifica el PORQUÉ comercial de cada mensaje entrante y calcula la Venta Potencial en Soles "
        "cruzando las piezas detectadas con los precios vigentes del almacén:"
    )
    add_table(
        ["Categoría Predicha", "Qué Significa para el Vendedor", "Nivel de Confianza y Venta Potencial", "Acción que Ejecuta el Sistema"],
        [
            [
                "COTIZACION (Azul)",
                "Oportunidad de venta inmediata: el cliente pregunta precio o disponibilidad de un repuesto.",
                "Muestra certeza (ej. 96.4%) y Venta Potencial (ej. S/ 185.00). Si es >= 68%, atiende 100% automático.",
                "Consulta stock en PostgreSQL, envía precio en Soles y datos de pago Yape/Plin (+51 937 395 986).",
            ],
            [
                "ESTADO_PEDIDO (Ámbar)",
                "Cierre post-pago: el cliente ya realizó un Yape/Plin o consulta el despacho de su orden.",
                "Alta prioridad comercial. Muestra el monto de la orden en curso para validación de caja.",
                "Prioriza el chat en la bandeja para validar el voucher y autorizar el despacho o recojo en Comas.",
            ],
            [
                "CONSULTA_TECNICA (Verde)",
                "Preventa mecánica: duda sobre si una pieza le calza a su modelo de mototaxi o moto lineal.",
                "Si la confianza es >= 82% responde automático; si es menor, activa 'Atención asistida'.",
                "Envía ficha de compatibilidad técnica, sugiere el repuesto en stock y avisa al especialista.",
            ],
            [
                "SPAM / No Deseado (Rojo)",
                "Publicidad externa, préstamos, sorteos o cadenas sin relación con la compra de repuestos.",
                "Exige certeza segura (>= 80%) y ausencia de intención de compra real (Precisión = 100%).",
                "Archiva el mensaje sin hacer sonar alertas en mostrador, ahorrando 48 horas/mes al equipo.",
            ],
        ],
        [1850, 2350, 2400, 2600],
    )

    add_image_compact(
        "rIdManual2",
        "image8.png",
        "Figura 2. Flujo del Asistente de WhatsApp (+51 937 395 986) cotizando stock real y métodos de pago.",
        max_w_emu=3900000,
        max_h_emu=1850000,
    )

    add_h1("4. ¿Qué hacer si el modelo falla o deriva a humano? (Degradación Controlada)")
    add_p(
        "El sistema cuenta con validaciones automáticas y un Protocolo de Degradación Controlada para que la tienda jamás pierda una venta ante mensajes ambiguos o interrupciones de red:"
    )
    add_table(
        ["Situación / Alerta en Pantalla", "Causa Técnica u Operativa", "Qué Ve el Usuario y Qué Debe Hacer el Vendedor"],
        [
            [
                "1. Etiqueta 'Derivado a Asesor de Ventas' (Confianza < 68%)",
                "El cliente mezcló dos consultas en un solo mensaje (ej. compatibilidad técnica + estado de un envío anterior).",
                "El bot envía una cotización referencial preventiva y marca el chat en ámbar. El vendedor debe abrir el chat en WhatsApp y responder la duda específica.",
            ],
            [
                "2. Aviso Rojo 'Entrada Inválida Rechazada'",
                "Se intentó clasificar un texto vacío, solo signos ('???') o una hora fuera del rango [0 a 23 horas].",
                "El sistema bloquea el envío erróneo con un mensaje claro en español. Ingrese una consulta válida con al menos una palabra o número.",
            ],
            [
                "3. Alerta 'DEGRADACIÓN CONTROLADA ACTIVADA (Fallback)'",
                "El servidor ML en Render está despertando (cold-start) o tardó más del límite permitido.",
                "El sistema aplica automáticamente la Regla Manual de Respaldo por palabras clave, envía acuse de recibo al cliente y deriva al celular +51 937 395 986 sin interrumpir la operación.",
            ],
        ],
        [2300, 2900, 4000],
    )

    doc_header = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'mc:Ignorable="w14 w15 wp14"><w:body>'
    )
    full_xml = doc_header + "\n".join(lines) + "\n" + sect_pr_xml + "</w:body></w:document>"
    ET.fromstring(full_xml.encode("utf-8"))
    (BUILD_DIR / "word" / "document.xml").write_text(full_xml, encoding="utf-8")

    out_paths = [
        ROOT_DIR / "PROY_TD_Grupo01_ManualUsuario.docx",
        ROOT_DIR / "Entregables_PROY_Semana17" / "PROY_TD_Grupo01_ManualUsuario.docx",
        ARTIFACT_DIR / "PROY_TD_Grupo01_ManualUsuario.docx",
    ]
    for p in out_paths:
        pack_docx(BUILD_DIR, p)
        print(f"[OK] Manual de Usuario creado en: {p} ({p.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build_manual()
