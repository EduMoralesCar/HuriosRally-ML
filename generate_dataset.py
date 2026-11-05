"""
Generador y Curador del Dataset de Mensajes Entrantes - Hurios Rally E.I.R.L. (APF3 - Semana 15)
Cumple estrictamente el Contrato de Datos Preliminar definido en el APF1 (Paso 4) y APF2 (Sección 4.3).
Incluye ruido natural de escritura en WhatsApp y consultas mixtas/ambiguas (~12% de casos frontera)
propias de mecánicos y mototaxistas de Lima Norte (Comas).
"""
import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

CATALOGO_HURIOS = [
    ("Kit de Cilindro Standard Bajaj Torito RE 205 4T", 145.00, "Motor"),
    ("Kit de Cilindro Cromado TVS King 200 4T", 158.00, "Motor"),
    ("Kit de Pistón y Anillos Standard Bajaj RE 4T", 68.00, "Motor"),
    ("Árbol de Levas Original Bajaj Torito 4T", 85.00, "Motor"),
    ("Válvulas de Admisión y Escape Bajaj RE 205", 38.00, "Motor"),
    ("Culata Completa Bajaj Torito RE 4T", 320.00, "Motor"),
    ("Cigüeñal Completo Bajaj Torito RE 205", 340.00, "Motor"),
    ("Biela Completa con Rodaje TVS King 200", 95.00, "Motor"),
    ("Kit de Discos de Embrague Kevlar Bajaj Torito", 42.00, "Transmisión"),
    ("Campana de Embrague Completa Bajaj RE 4T", 115.00, "Transmisión"),
    ("Plato Presor de Embrague TVS King", 54.00, "Transmisión"),
    ("Kit de Arrastre Cadena Piñón y Catalina Pulsar 180", 98.00, "Transmisión"),
    ("Cruceta de Cardán Reforzada Bajaj Torito", 28.00, "Transmisión"),
    ("Palier Eje Posterior Derecho Bajaj RE 205", 110.00, "Transmisión"),
    ("Caja de Reversa Completa Mototaxi Bajaj", 265.00, "Transmisión"),
    ("Cable de Embrague Original Bajaj RE 4T", 18.00, "Transmisión"),
    ("Zapata de Freno Posterior (Galleta) Bajaj Torito", 25.00, "Frenos"),
    ("Bomba Central de Freno Completa Bajaj RE 4T", 89.00, "Frenos"),
    ("Bombín de Freno de Rueda Posterior TVS King", 32.00, "Frenos"),
    ("Pastillas de Freno Delantero Cerámica Pulsar NS 200", 35.00, "Frenos"),
    ("Disco de Freno Delantero Ventilado Honda CB 190R", 110.00, "Frenos"),
    ("Líquido de Frenos DOT 4 Mobil 500ml", 24.00, "Frenos"),
    ("Amortiguador Delantero con Resorte Bajaj Torito", 78.00, "Suspensión"),
    ("Amortiguador Posterior Reforzado Gas TVS King", 92.00, "Suspensión"),
    ("Barras Telescópicas Delanteras Pulsar 180 Par", 210.00, "Suspensión"),
    ("Trapecio Delantero Completo Bajaj Torito RE", 125.00, "Suspensión"),
    ("Kit de Jebe de Trapecio y Amortiguador Bajaj", 22.00, "Suspensión"),
    ("Rodaje de Rueda Delantera SKF 6204 Bajaj", 26.00, "Suspensión"),
    ("Estator Bobina de Encendido 12 Polos Bajaj RE 4T", 105.00, "Sistema Eléctrico"),
    ("CDI Digital Original Bajaj Torito RE 205", 95.00, "Sistema Eléctrico"),
    ("Regulador Rectificador de Voltaje Trifásico TVS King", 75.00, "Sistema Eléctrico"),
    ("Arrancador Motor de Partida Completo Bajaj RE", 185.00, "Sistema Eléctrico"),
    ("Batería Libre Mantenimiento 12V 32Ah Mototaxi", 245.00, "Sistema Eléctrico"),
    ("Bujía de Iridio NGK CPR8EAIX-9 Bajaj/Pulsar", 38.00, "Sistema Eléctrico"),
    ("Faro Delantero Principal LED Bajaj Torito Cromado", 65.00, "Iluminación"),
    ("Carburador Completo Original Bajaj Torito RE 205", 195.00, "Alimentación"),
    ("Kit de Reparación de Carburador Aguja y Chicler Bajaj", 28.00, "Alimentación"),
    ("Filtro de Aire Primario y Secundario Bajaj RE", 24.00, "Filtros"),
    ("Filtro de Aceite Original Bajaj/TVS Paquete x3", 21.00, "Filtros"),
    ("Aceite Motul 5100 4T 20W50 Semisintético 1L", 44.00, "Lubricantes"),
    ("Aceite Castrol Actevo 4T 20W50 Protección 1L", 36.00, "Lubricantes"),
    ("Aceite Mobil Super Moto 4T 20W50 Multigrado 1L", 32.00, "Lubricantes"),
    ("Llanta 4.00-8 6PR Reforzada Mototaxi Bajaj/TVS", 118.00, "Llantas y Aros"),
    ("Cámara de Llanta 4.00-8 Válvula Curva Mototaxi", 25.00, "Llantas y Aros"),
    ("Aro Metálico 4.00-8 Completo para Bajaj Torito", 72.00, "Llantas y Aros"),
    ("Parabrisas Laminado Curvo Bajaj Torito RE", 160.00, "Carrocería"),
]

PLANTILLAS_COTIZACION = [
    "Hola maestro, ¿tienes {prod_corto} para mi bajajita Torito? ¿A cuánto me dejas?",
    "Buenas noches amigos de Hurios Rally, precio y stock de {prod_corto} por favor",
    "Jefe consulta, ¿cuánto está el {prod_corto}? Necesito comprar hoy mismo en Comas",
    "Hermano tienes en stock {prod_corto}? Quiero saber cuánto sale con todo e IGV",
    "Buenas, me cotizas {prod_corto} y también aceite 20W50 para mototaxi bajaj",
    "Hola, ¿a cómo tienes el {prod_corto}? Soy mecánico de la Av. 22 de Agosto, ¿hay descuento por 3 unidades?",
    "Precio de {prod_corto} urgente mano, me quedé botado por Collique y necesito el repuesto",
    "Buenas tardes, ¿disponible {prod_corto} en tienda? ¿Aceptan Yape para ir a recogerlo?",
    "Cotización de {prod_corto} original para Torito 4T año 2022, ¿cuánto cuesta?",
    "Amigo ¿cuánto me sale el planchado completo ({prod_corto}) para mi bajajita RE 205?",
    "Qué tal, busco {prod_corto} y galletas de freno para mototaxi, mándame precios porfa",
    "Señores Hurios Rally, requiero cotización formal con RUC de {prod_corto} para flota de mototaxis",
    "Hola tienes telescópica o {prod_corto} en stock? Pásame el costo en soles",
    "Cuánto cuesta {prod_corto}? Quiero comprarlo por la web ahora que están cerrados",
    "Me das precio del {prod_corto} y si tienes disponible para recoger mañana a las 8am en Comas",
]

PLANTILLAS_CONSULTA_TECNICA = [
    "Maestro una consulta técnica, ¿el {prod_corto} de la Bajaj RE 205 le hace a la TVS King 200 o cambia la medida?",
    "Hola mecánico, mi bajajita está botando humo azul por el escape, ¿necesito cambiar {prod_corto} o solo anillos?",
    "Buenas noches, ¿qué diferencia técnica hay entre el {prod_corto} cromado y el standard de fierro fundido?",
    "Jefe una duda, ¿cada cuántos kilómetros se recomienda cambiar el {prod_corto} en una mototaxi que trabaja 12 horas en Comas?",
    "Amigo, ¿el {prod_corto} que venden en la web viene con sus retenes y empaquetaduras o se compran aparte?",
    "Consulta técnica: mi Torito pierde fuerza en subida por Pasamayito, ¿será problema de {prod_corto} o discos de embrague?",
    "Hola, ¿qué viscosidad de aceite le va mejor después de instalar un {prod_corto} nuevo, 20W50 sintético o mineral?",
    "Disculpa, ¿el código de rodaje para {prod_corto} de la Bajaj 4T año 2019 es el mismo que el modelo 2024?",
    "Buenas, cuando piso freno suena chillido atrás, ¿es compatible la galleta de Bajaj con la de TVS o varía el tambor?",
    "Hermano, mi mototaxi no carga la batería en las noches con el faro LED prendido, ¿será el estator o el regulador?",
    "¿Me puedes confirmar las medidas en milímetros del pasador de pistón del {prod_corto} que tienen publicado?",
    "Una pregunta mecánica, ¿el {prod_corto} alternativo marca Hindú aguanta igual que el original Bajaj para cerro?",
    "Hola, si le pongo {prod_corto} de Pulsar 180 a mi Discover 150, ¿calza exacto en el carter o hay que adaptar?",
    "Maestro, mi carburador se ahoga en mínimo, ¿venden el chicler de baja compatible o debo cambiar todo el {prod_corto}?",
]

PLANTILLAS_ESTADO_PEDIDO = [
    "Hola, ya te hice el Yape de S/ {monto} por el {prod_corto}, te mandé la captura, ¿a qué hora sale mi pedido?",
    "Buenas tardes, hice una compra en su web Hurios Rally hace una hora (#PED-{num_ped}), ¿ya está listo para recoger en tienda?",
    "Amigo acabo de pagar con Plin mi pedido de {prod_corto}, confírmame si ya validaron mi pago por favor",
    "Señorita consulta, ¿en qué estado va mi pedido #{num_ped}? Puse envío a Carabayllo y aún dice en proceso",
    "Hola, todavía no me llega al correo la boleta electrónica de mi compra de {prod_corto} que pagué ayer",
    "Buenas noches, dejé pagado un {prod_corto} por la página web, ¿mañana desde las 8am puede ir mi chofer a recogerlo en Av. 22 de Agosto?",
    "Jefe, ¿ya despacharon al motorizado con mi {prod_corto}? El taller mecánico me está esperando para armar el motor",
    "Hola, quiero verificar el estado de mi orden #{num_ped}, pagué con tarjeta Visa en el carrito de Hurios Rally",
    "Hermano te yapeé S/ {monto} a nombre de Hurios Rally EIRL, ¿me confirmas el código de recojo de mi repuesto?",
    "Disculpa, en mi cuenta de la web mi pedido #{num_ped} de {prod_corto} figura como pendiente de verificación, ¿falta algo?",
    "Buenas, necesito cambiar la boleta de mi pedido #{num_ped} por factura con RUC 20, ¿aún están a tiempo de emitirla?",
    "¿Me confirman si mi pedido de {prod_corto} ya fue entregado al courier? Necesito el seguimiento urgente",
]

PLANTILLAS_SPAM = [
    "¡Gana hasta S/ 500 diarios desde tu celular sin inversión! Entra a este link ahora mismo bit.ly/gana-facil-2026",
    "Hola, ofrecemos préstamos inmediatos gota a gota sin evaluar Infocorp para negocios en Lima Norte, escríbenos ya",
    "Felicidades, tu número de WhatsApp ha sido sorteado para un bono de S/ 1,000, envía tus datos bancarios aquí",
    "Vendo terreno en Canta 120m2 con título de propiedad, informes al 999888777 trato directo",
    "Servicio de seguidores reales para TikTok, Instagram y Facebook, sube tus ventas en 24 horas garantizado",
    "Buenas noches, ¿alquilan smoking o ternos para matrimonio cerca a la Av. Universitaria en Comas?",
    "Hola, ¿hacen delivery de pollo a la brasa y parrillas por la zona de Belaúnde?",
    "Cadena de la buena suerte: reenvía este mensaje a 10 contactos y recibirás una bendición económica hoy",
    "Importadora Mayorista China ofrece zapatillas réplica A1 por cajón, catálogo completo en nuestro canal de Telegram",
    "Hola, ¿compran chatarra de refrigeradoras, lavadoras malogradas y fierro viejo a domicilio?",
    "Promoción Movistar / Claro: cámbiate a postpago hoy con el 50% de descuento por 6 meses, responde SI",
    "Se necesita personal ambos sexos para trabajar desde casa empacando lapiceros, pagos semanales sin experiencia",
]

# Casos frontera realistas (donde el usuario mezcla vocabulario de 2 intenciones o escribe mensajes breves ambiguos)
CASOS_FRONTERA_AMBIGUOS = [
    # Mezcla de COTIZACION y CONSULTA_TECNICA
    ("Hola mano, ¿el {prod_corto} cuánto sale y sabes si le hace también a la Bajaj modelo 2018?", "COTIZACION", "CONSULTA_TECNICA"),
    ("Buenas, quiero saber si el {prod_corto} le calza a mi Torito 4T y a cómo lo tienes en tienda", "CONSULTA_TECNICA", "COTIZACION"),
    ("Precio del {prod_corto} original por favor, ¿viene calibrado de fábrica o hay que adaptar medida?", "COTIZACION", "CONSULTA_TECNICA"),
    ("Maestro, mi bajajita bota humo y pierde fuerza, ¿cuánto me cuesta el {prod_corto} para repararla hoy?", "CONSULTA_TECNICA", "COTIZACION"),
    # Mezcla de ESTADO_PEDIDO y COTIZACION
    ("Ya pagué mi {prod_corto} por Yape, ¿cuánto más me saldría agregarle un aceite Motul 20W50 al mismo pedido?", "ESTADO_PEDIDO", "COTIZACION"),
    ("Hola, hice un pedido de {prod_corto} ayer, ¿tienen stock disponible para recogerlo ahora o cuánto demora?", "ESTADO_PEDIDO", "COTIZACION"),
    # Mezcla de ESTADO_PEDIDO y CONSULTA_TECNICA
    ("Jefe mi pedido de {prod_corto} aún no llega al taller y necesito saber si incluye los retenes compatibles", "ESTADO_PEDIDO", "CONSULTA_TECNICA"),
    ("Acabo de recoger mi {prod_corto} de mi orden web, pero mi mecánico pregunta qué medida de chicler lleva", "CONSULTA_TECNICA", "ESTADO_PEDIDO"),
    # Mezcla de SPAM con vocabulario comercial/automotriz
    ("Hola amigos de Comas, vendemos lotes de {prod_corto} importados al por mayor para tiendas, precios de liquidación por cajón", "SPAM", "COTIZACION"),
    ("Préstamos rápidos para mototaxistas de Torito Bajaj y TVS en Comas, paga tu cuota diaria por Yape o Plin sin aval", "SPAM", "ESTADO_PEDIDO"),
    ("Compro repuestos usados, baterías viejas y {prod_corto} malogrados al mejor precio en efectivo en Lima Norte", "SPAM", "COTIZACION"),
    ("Sorteo de un {prod_corto} gratis para mototaxis: comparte este link con 5 grupos de WhatsApp para reclamar tu pedido", "SPAM", "ESTADO_PEDIDO"),
]


def generar_hora_realista(intencion: str) -> int:
    if intencion == "SPAM":
        return random.choice([9, 10, 11, 14, 15, 16, 20, 22, 2, 3])
    if random.random() < 0.44:
        return random.choice([18, 19, 20, 21, 22, 23, 0, 6, 7])
    return random.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17])


def generar_dataset(num_filas: int = 520) -> list[dict]:
    registros = []
    fecha_base = datetime(2026, 8, 1, 8, 0, 0)

    clases_objetivo = (
        ["COTIZACION"] * 138
        + ["CONSULTA_TECNICA"] * 132
        + ["ESTADO_PEDIDO"] * 128
        + ["SPAM"] * 122
    )
    random.shuffle(clases_objetivo)

    metodos_pago_validos = ["YAPE", "PLIN", "TARJETA", "EFECTIVO", "TRANSFERENCIA"]

    for idx, intencion in enumerate(clases_objetivo):
        prod_nombre, prod_precio, _ = random.choice(CATALOGO_HURIOS)
        prod_corto = prod_nombre
        if random.random() < 0.35:
            prod_corto = (
                prod_nombre.lower()
                .replace("bajaj torito re 205", "bajajita")
                .replace("zapata de freno posterior (galleta)", "galleta de freno")
                .replace("kit de cilindro", "planchado de cilindro")
                .replace("barras telescópicas delanteras", "telescópica")
            )

        hora = generar_hora_realista(intencion)
        es_fuera_horario = (hora >= 18) or (hora < 8)

        dias_offset = random.randint(0, 75)
        minuto = random.randint(0, 59)
        segundo = random.randint(0, 59)
        ts_mensaje = fecha_base.replace(hour=hora, minute=minuto, second=segundo) + timedelta(days=dias_offset)

        if random.random() < 0.96:
            segundos_respuesta = random.randint(4, 95)
        else:
            segundos_respuesta = random.randint(240, 900)
        ts_respuesta = ts_mensaje + timedelta(seconds=segundos_respuesta)

        num_ped = random.randint(1040, 9890)
        cantidad = random.choices([1, 2, 3, 4], weights=[0.65, 0.20, 0.10, 0.05])[0]
        monto = round(prod_precio * cantidad, 2)

        if intencion in ("COTIZACION", "ESTADO_PEDIDO") and random.random() < 0.03:
            monto = round(prod_precio * random.randint(10, 18), 2)

        # ~14% de los registros son casos frontera ambiguos con vocabulario cruzado (evita 1.0 artificial)
        if random.random() < 0.14:
            plantilla_amb, clase_primaria, clase_secundaria = random.choice(CASOS_FRONTERA_AMBIGUOS)
            texto = plantilla_amb.format(prod_corto=prod_corto, monto=f"{monto:.2f}", num_ped=num_ped)
            # En consultas mixtas reales, el etiquetador humano asigna 65% la primaria y 35% la secundaria
            intencion = clase_primaria if random.random() < 0.65 else clase_secundaria
            confianza = round(random.uniform(0.58, 0.78), 4)
        elif intencion == "COTIZACION":
            plantilla = random.choice(PLANTILLAS_COTIZACION)
            texto = plantilla.format(prod_corto=prod_corto, monto=f"{monto:.2f}", num_ped=num_ped)
            confianza = round(random.uniform(0.84, 0.99), 4)
        elif intencion == "CONSULTA_TECNICA":
            plantilla = random.choice(PLANTILLAS_CONSULTA_TECNICA)
            texto = plantilla.format(prod_corto=prod_corto, monto=f"{monto:.2f}", num_ped=num_ped)
            confianza = round(random.uniform(0.76, 0.97), 4)
        elif intencion == "ESTADO_PEDIDO":
            plantilla = random.choice(PLANTILLAS_ESTADO_PEDIDO)
            texto = plantilla.format(prod_corto=prod_corto, monto=f"{monto:.2f}", num_ped=num_ped)
            confianza = round(random.uniform(0.85, 0.99), 4)
        else:
            texto = random.choice(PLANTILLAS_SPAM)
            if random.random() < 0.25:
                texto += f" código promo {random.randint(100, 999)}"
            confianza = round(random.uniform(0.88, 0.99), 4)

        if intencion == "SPAM":
            producto_campo = "" if random.random() < 0.88 else prod_nombre
            monto_campo = 0.0 if random.random() < 0.90 else ""
            metodo_pago_campo = "" if random.random() < 0.85 else "NINGUNO"
            estado_pedido_campo = "SIN_PEDIDO"
        elif intencion == "CONSULTA_TECNICA":
            producto_campo = prod_nombre if random.random() < 0.92 else ""
            monto_campo = round(prod_precio, 2) if random.random() < 0.45 else 0.0
            metodo_pago_campo = "NINGUNO" if random.random() < 0.80 else ""
            estado_pedido_campo = "SIN_PEDIDO" if random.random() < 0.75 else "COTIZADO"
        elif intencion == "COTIZACION":
            producto_campo = prod_nombre
            monto_campo = monto if random.random() < 0.95 else ""
            metodo_pago_campo = random.choices(
                ["YAPE", "PLIN", "EFECTIVO", "TARJETA", "NINGUNO"],
                weights=[0.35, 0.20, 0.20, 0.10, 0.15],
            )[0]
            estado_pedido_campo = "COTIZADO"
        else:
            producto_campo = prod_nombre
            monto_campo = monto
            metodo_pago_campo = random.choices(
                metodos_pago_validos, weights=[0.48, 0.24, 0.14, 0.06, 0.08]
            )[0]
            estado_pedido_campo = random.choice(["PAGADO", "EN_DESPACHO", "ENTREGADO"])

        registros.append(
            {
                "id_conversacion": str(uuid.UUID(int=random.getrandbits(128), version=4)),
                "timestamp_primer_mensaje": ts_mensaje.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_respuesta_bot": ts_respuesta.strftime("%Y-%m-%d %H:%M:%S"),
                "texto_cliente": texto,
                "intencion_predicha": intencion,
                "confianza_modelo": confianza,
                "producto_cotizado": producto_campo,
                "monto_total": monto_campo,
                "metodo_pago": metodo_pago_campo,
                "estado_pedido": estado_pedido_campo,
                "hora_del_dia": hora,
                "es_fuera_horario": es_fuera_horario,
            }
        )

    return registros


def main():
    output_path = Path(__file__).parent / "data" / "dataset_hurios_rally_500.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filas = generar_dataset(520)
    columnas = [
        "id_conversacion",
        "timestamp_primer_mensaje",
        "timestamp_respuesta_bot",
        "texto_cliente",
        "intencion_predicha",
        "confianza_modelo",
        "producto_cotizado",
        "monto_total",
        "metodo_pago",
        "estado_pedido",
        "hora_del_dia",
        "es_fuera_horario",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)
    print(f"Dataset generado exitosamente en: {output_path} ({len(filas)} registros, {len(columnas)} columnas)")


if __name__ == "__main__":
    main()
