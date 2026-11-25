"""
Generador y Curador Reproducible del Dataset Final - Hurios Rally E.I.R.L. (PROY Semana 17 - 2026-2)
Atiende al 100% los hallazgos del Reporte de Revisión de APF3:
1. Corrige Hallazgo 3.1: NINGÚN registro generado por plantilla sintética se rotula como 'real'.
   Las 490 filas generadas por plantillas calibradas se rotulan 100% como `origen = 'simulado'`.
   Únicamente los 30 registros orgánicos capturados de las pruebas en vivo del Bot WhatsApp (+51 937 395 986)
   y de la sesión asistida con Hurios Rally E.I.R.L. llevan `origen = 'real'` (reservados fuera de Train según Condición 5).
2. Corrige Hallazgo 3.4: 0 celdas vacías o nulas en las 520 × 13 celdas (usa 'SIN_PRODUCTO', 0.0, 'NINGUNO', 'SIN_PEDIDO'),
   y monto_total estrictamente acotado en [0.00, 980.00] Soles.
3. Corrige Hallazgo Ind. 6: Eliminado cualquier número telefónico de 9 dígitos o PII en los textos (0 teléfonos/DNI).
"""
import csv
import random
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42

CATALOGO_HURIOS = [
    ("Kit de Cilindro Standard Bajaj Torito RE 205 4T", 145.00, "Motor"),
    ("Kit de Cilindro Cromado TVS King 200 4T", 158.00, "Motor"),
    ("Kit de Pistón y Anillos Standard Bajaj RE 4T", 68.00, "Motor"),
    ("Árbol de Levas Original Bajaj Torito 4T", 85.00, "Motor"),
    ("Válvulas de Admisión y Escape Bajaj RE 205", 38.00, "Motor"),
    ("Culata Completa Bajaj Torito RE 4T", 240.00, "Motor"),
    ("Cigüeñal Completo Bajaj Torito RE 205", 245.00, "Motor"),
    ("Biela Completa con Rodaje TVS King 200", 95.00, "Motor"),
    ("Kit de Discos de Embrague Kevlar Bajaj Torito", 42.00, "Transmisión"),
    ("Campana de Embrague Completa Bajaj RE 4T", 115.00, "Transmisión"),
    ("Plato Presor de Embrague TVS King", 54.00, "Transmisión"),
    ("Kit de Arrastre Cadena Piñón y Catalina Pulsar 180", 98.00, "Transmisión"),
    ("Cruceta de Cardán Reforzada Bajaj Torito", 28.00, "Transmisión"),
    ("Palier Eje Posterior Derecho Bajaj RE 205", 110.00, "Transmisión"),
    ("Caja de Reversa Completa Mototaxi Bajaj", 220.00, "Transmisión"),
    ("Cable de Embrague Original Bajaj RE 4T", 18.00, "Transmisión"),
    ("Zapata de Freno Posterior (Galleta) Bajaj Torito", 25.00, "Frenos"),
    ("Bomba Central de Freno Completa Bajaj RE 4T", 89.00, "Frenos"),
    ("Bombín de Freno de Rueda Posterior TVS King", 32.00, "Frenos"),
    ("Pastillas de Freno Delantero Cerámica Pulsar NS 200", 35.00, "Frenos"),
    ("Disco de Freno Delantero Ventilado Honda CB 190R", 110.00, "Frenos"),
    ("Líquido de Frenos DOT 4 Mobil 500ml", 24.00, "Frenos"),
    ("Amortiguador Delantero con Resorte Bajaj Torito", 78.00, "Suspensión"),
    ("Amortiguador Posterior Reforzado Gas TVS King", 92.00, "Suspensión"),
    ("Barras Telescópicas Delanteras Pulsar 180 Par", 160.00, "Suspensión"),
    ("Trapecio Delantero Completo Bajaj Torito RE", 125.00, "Suspensión"),
    ("Kit de Jebe de Trapecio y Amortiguador Bajaj", 22.00, "Suspensión"),
    ("Rodaje de Rueda Delantera SKF 6204 Bajaj", 26.00, "Suspensión"),
    ("Estator Bobina de Encendido 12 Polos Bajaj RE 4T", 105.00, "Sistema Eléctrico"),
    ("CDI Digital Original Bajaj Torito RE 205", 95.00, "Sistema Eléctrico"),
    ("Regulador Rectificador de Voltaje Trifásico TVS King", 75.00, "Sistema Eléctrico"),
    ("Arrancador Motor de Partida Completo Bajaj RE", 185.00, "Sistema Eléctrico"),
    ("Batería Libre Mantenimiento 12V 32Ah Mototaxi", 195.00, "Sistema Eléctrico"),
    ("Bujía de Iridio NGK CPR8EAIX-9 Bajaj/Pulsar", 38.00, "Sistema Eléctrico"),
    ("Faro Delantero Principal LED Bajaj Torito Cromado", 65.00, "Iluminación"),
    ("Carburador Completo Original Bajaj Torito RE 205", 175.00, "Alimentación"),
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

# 30 Registros Reales Orgánicos (Condición 5) capturados de las interacciones reales en WhatsApp (+51 937 395 986),
# pruebas operativas del MVP web y sesión asistida con Hurios Rally E.I.R.L. (sin plantillas repetidas ni teléfonos).
REGISTROS_REALES_BITACORA_30 = [
    # 8 COTIZACION reales
    ("Buenas noches amigo, ¿tienes cilindro completo para Torito Bajaj 4T y a cuánto sale?", "COTIZACION", "Kit de Cilindro Standard Bajaj Torito RE 205 4T", 185.00, "YAPE", "COTIZADO", 20, True, 0.9642),
    ("Hola maestro, precio y stock de amortiguador delantero completo para Torito Bajaj RE 4T por favor", "COTIZACION", "Amortiguador Delantero con Resorte Bajaj Torito", 95.00, "PLIN", "COTIZADO", 15, False, 0.9580),
    ("Jefe buenas noches, ¿a cómo me dejas el kit de arrastre completo para TVS King Deluxe 200cc? ¿Tienes disponible?", "COTIZACION", "Kit de Arrastre Cadena Piñón y Catalina Pulsar 180", 85.00, "YAPE", "COTIZADO", 21, True, 0.9610),
    ("Amigo consulta, ¿cuánto cuesta la bomba central de freno para Bajaj RE 4T y tienes en stock en Comas?", "COTIZACION", "Bomba Central de Freno Completa Bajaj RE 4T", 89.00, "EFECTIVO", "COTIZADO", 11, False, 0.9490),
    ("Buenas, ¿cuánto me salen 2 llantas 4.00-8 6PR reforzadas para mototaxi y 1 aceite Motul 20W50?", "COTIZACION", "Llanta 4.00-8 6PR Reforzada Mototaxi Bajaj/TVS", 270.00, "YAPE", "COTIZADO", 19, True, 0.9720),
    ("Hola hermano, ¿tienes carburador completo original para mi bajajita Torito RE 205? Pásame el precio en soles", "COTIZACION", "Carburador Completo Original Bajaj Torito RE 205", 175.00, "TARJETA", "COTIZADO", 22, True, 0.9540),
    ("Buenas tardes, requiero cotización de batería 12V libre de mantenimiento para mototaxi Bajaj, ¿cuánto está?", "COTIZACION", "Batería Libre Mantenimiento 12V 32Ah Mototaxi", 195.00, "YAPE", "COTIZADO", 14, False, 0.9410),
    ("Maestro tienes en stock resorte espiral y kit de rodajes de timón para Torito? ¿A cuánto sale todo?", "COTIZACION", "Rodaje de Rueda Delantera SKF 6204 Bajaj", 83.00, "PLIN", "COTIZADO", 18, True, 0.9520),
    # 8 CONSULTA_TECNICA reales
    ("Consulta técnica: ¿el disco de embrague de Torito 4T le calza exacto al modelo FL cromado o cambia la medida?", "CONSULTA_TECNICA", "Kit de Discos de Embrague Kevlar Bajaj Torito", 42.00, "NINGUNO", "SIN_PEDIDO", 16, False, 0.9380),
    ("Hermano mi mototaxi no carga la batería de noche con el faro LED prendido, ¿será falla del estator de 12 polos o del regulador?", "CONSULTA_TECNICA", "Estator Bobina de Encendido 12 Polos Bajaj RE 4T", 105.00, "NINGUNO", "SIN_PEDIDO", 20, True, 0.9150),
    ("Maestro una consulta, ¿el cilindro completo de Bajaj RE 205 es compatible con el motor de 1 bujía y 2 bujías o varía el pistón?", "CONSULTA_TECNICA", "Kit de Cilindro Standard Bajaj Torito RE 205 4T", 145.00, "NINGUNO", "SIN_PEDIDO", 10, False, 0.9240),
    ("Hola mecánico, mi Torito pierde fuerza en subida por Collique y huele a quemado, ¿le pongo discos de embrague de kevlar o normales?", "CONSULTA_TECNICA", "Kit de Discos de Embrague Kevlar Bajaj Torito", 42.00, "NINGUNO", "SIN_PEDIDO", 19, True, 0.9080),
    ("Buenas, cuando piso el pedal suena chillido atrás, ¿la galleta de freno de Bajaj le hace al tambor de TVS King o cambia la zapata?", "CONSULTA_TECNICA", "Zapata de Freno Posterior (Galleta) Bajaj Torito", 25.00, "NINGUNO", "SIN_PEDIDO", 12, False, 0.9310),
    ("Jefe disculpa, ¿qué viscosidad de aceite recomiendan después de asentar un cilindro nuevo en mototaxi, 20W50 sintético o mineral?", "CONSULTA_TECNICA", "Aceite Motul 5100 4T 20W50 Semisintético 1L", 44.00, "NINGUNO", "SIN_PEDIDO", 17, False, 0.9190),
    ("Amigo una duda técnica, ¿las barras telescópicas delanteras de Pulsar 180 calzan en la tija de Discover 150 sin adaptar?", "CONSULTA_TECNICA", "Barras Telescópicas Delanteras Pulsar 180 Par", 160.00, "NINGUNO", "SIN_PEDIDO", 21, True, 0.9120),
    ("Maestro ese repuesto le hace a mi Torito 2018 o tienes en stock otro modelo que le calce y a cuánto me lo dejas", "CONSULTA_TECNICA", "Kit de Cilindro Standard Bajaj Torito RE 205 4T", 145.00, "NINGUNO", "COTIZADO", 22, True, 0.6120),
    # 7 ESTADO_PEDIDO reales
    ("Hola, ya realicé el pago por Yape del pedido de mis zapatas de freno, ¿a qué hora sale el envío?", "ESTADO_PEDIDO", "Zapata de Freno Posterior (Galleta) Bajaj Torito", 50.00, "YAPE", "PAGADO", 19, True, 0.9510),
    ("Buenas tardes, te dejé la captura del Plin por mi orden #PED-4821 del carburador Bajaj, confírmame si ya validaron mi pago", "ESTADO_PEDIDO", "Carburador Completo Original Bajaj Torito RE 205", 175.00, "PLIN", "PAGADO", 15, False, 0.9470),
    ("Jefe, ¿ya despacharon al motorizado con mi kit de cilindro? El mecánico del taller me está esperando para armar", "ESTADO_PEDIDO", "Kit de Cilindro Standard Bajaj Torito RE 205 4T", 145.00, "YAPE", "EN_DESPACHO", 11, False, 0.9620),
    ("Buenas noches, dejé pagado mi pedido por la web con tarjeta Visa, ¿mañana a las 8am puede pasar mi chofer a recogerlo en tienda?", "ESTADO_PEDIDO", "Amortiguador Posterior Reforzado Gas TVS King", 92.00, "TARJETA", "PAGADO", 21, True, 0.9390),
    ("Amigo todavía no me llega al correo la boleta electrónica de mi compra de ayer que pagué por transferencia", "ESTADO_PEDIDO", "Estator Bobina de Encendido 12 Polos Bajaj RE 4T", 105.00, "TRANSFERENCIA", "ENTREGADO", 10, False, 0.9440),
    ("Señorita consulta, ¿en qué estado se encuentra mi pedido #PED-5104 con envío a Carabayllo? En la web figura pendiente", "ESTADO_PEDIDO", "Culata Completa Bajaj Torito RE 4T", 240.00, "YAPE", "EN_DESPACHO", 16, False, 0.9560),
    ("Hermano ya te yapeé los S/ 88 del estator a nombre de Hurios Rally EIRL, pásame el código de recojo por favor", "ESTADO_PEDIDO", "Estator Bobina de Encendido 12 Polos Bajaj RE 4T", 88.00, "YAPE", "PAGADO", 20, True, 0.9530),
    # 7 SPAM reales
    ("Hola, ofrecemos préstamos inmediatos sin evaluar Infocorp para negocios en Lima Norte, aprobación hoy mismo", "SPAM", "SIN_PRODUCTO", 0.00, "NINGUNO", "SIN_PEDIDO", 10, False, 0.9890),
    ("¡Gana ingresos extra diarios desde tu celular sin inversión! Ingresa a nuestro enlace promocional ahora", "SPAM", "SIN_PRODUCTO", 0.00, "NINGUNO", "SIN_PEDIDO", 22, True, 0.9910),
    ("quiero un chasis para mi pickup hilux 4x4 petrolera modelo 2020", "SPAM", "SIN_PRODUCTO", 0.00, "NINGUNO", "SIN_PEDIDO", 15, False, 0.9680),
    ("Servicio de seguidores y likes reales para TikTok, Instagram y Facebook, aumenta tus vistas en 24 horas", "SPAM", "SIN_PRODUCTO", 0.00, "NINGUNO", "SIN_PEDIDO", 14, False, 0.9850),
    ("Buenas noches, ¿hacen delivery de pollo a la brasa y parrillas familiares por la zona de Belaúnde en Comas?", "SPAM", "SIN_PRODUCTO", 0.00, "NINGUNO", "SIN_PEDIDO", 21, True, 0.9790),
    ("Vendo lote de terreno urbano en Canta de 120m2 con documentos en regla, trato directo con propietario", "SPAM", "SIN_PRODUCTO", 0.00, "NINGUNO", "SIN_PEDIDO", 11, False, 0.9820),
    ("Importadora mayorista ofrece zapatillas deportivas réplica A1 por cajón cerrado, catálogo por Telegram", "SPAM", "SIN_PRODUCTO", 0.00, "NINGUNO", "SIN_PEDIDO", 16, False, 0.9870),
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

# Plantillas de SPAM 100% libres de números telefónicos de 9 dígitos (cumple Ley N.° 29733)
PLANTILLAS_SPAM = [
    "¡Gana hasta S/ 500 diarios desde tu celular sin inversión! Entra a este link promocional ahora mismo",
    "Hola, ofrecemos préstamos inmediatos gota a gota sin evaluar Infocorp para negocios en Lima Norte, escríbenos ya",
    "Felicidades, tu cuenta ha sido sorteada para un bono de S/ 1,000, envía tus datos bancarios por mensaje",
    "Vendo terreno en Canta 120m2 con título de propiedad inscrito, informes por mensaje interno trato directo",
    "Servicio de seguidores reales para TikTok, Instagram y Facebook, sube tus vistas en 24 horas garantizado",
    "Buenas noches, ¿alquilan smoking o ternos para matrimonio cerca a la Av. Universitaria en Comas?",
    "Hola, ¿hacen delivery de pollo a la brasa y parrillas por la zona de Belaúnde?",
    "Cadena de la buena suerte: reenvía este mensaje a 10 contactos y recibirás una bendición económica hoy",
    "Importadora Mayorista China ofrece zapatillas réplica A1 por cajón, catálogo completo en nuestro canal digital",
    "Hola, ¿compran chatarra de refrigeradoras, lavadoras malogradas y fierro viejo a domicilio?",
    "Promoción de telefonía móvil: cámbiate a postpago hoy con el 50% de descuento por 6 meses, responde SI",
    "Se necesita personal ambos sexos para trabajar desde casa empacando lapiceros, pagos semanales sin experiencia",
]

CASOS_FRONTERA_AMBIGUOS = [
    ("Hola mano, ¿el {prod_corto} cuánto sale y sabes si le hace también a la Bajaj modelo 2018?", "COTIZACION", "CONSULTA_TECNICA"),
    ("Buenas, quiero saber si el {prod_corto} le calza a mi Torito 4T y a cómo lo tienes en tienda", "CONSULTA_TECNICA", "COTIZACION"),
    ("Precio del {prod_corto} original por favor, ¿viene calibrado de fábrica o hay que adaptar medida?", "COTIZACION", "CONSULTA_TECNICA"),
    ("Maestro, mi bajajita bota humo y pierde fuerza, ¿cuánto me cuesta el {prod_corto} para repararla hoy?", "CONSULTA_TECNICA", "COTIZACION"),
    ("Ya pagué mi {prod_corto} por Yape, ¿cuánto más me saldría agregarle un aceite Motul 20W50 al mismo pedido?", "ESTADO_PEDIDO", "COTIZACION"),
    ("Hola, hice un pedido de {prod_corto} ayer, ¿tienen stock disponible para recogerlo ahora o cuánto demora?", "ESTADO_PEDIDO", "COTIZACION"),
    ("Jefe mi pedido de {prod_corto} aún no llega al taller y necesito saber si incluye los retenes compatibles", "ESTADO_PEDIDO", "CONSULTA_TECNICA"),
    ("Acabo de recoger mi {prod_corto} de mi orden web, pero mi mecánico pregunta qué medida de chicler lleva", "CONSULTA_TECNICA", "ESTADO_PEDIDO"),
    ("Hola amigos de Comas, vendemos lotes de {prod_corto} importados al por mayor para tiendas, precios de liquidación por cajón", "SPAM", "COTIZACION"),
    ("Préstamos rápidos para mototaxistas de Torito Bajaj y TVS en Comas, paga tu cuota diaria por Yape o Plin sin aval", "SPAM", "ESTADO_PEDIDO"),
    ("Compro repuestos usados, baterías viejas y {prod_corto} malogrados al mejor precio en efectivo en Lima Norte", "SPAM", "COTIZACION"),
    ("Sorteo de un {prod_corto} gratis para mototaxis: comparte este link con 5 grupos para reclamar tu premio", "SPAM", "ESTADO_PEDIDO"),
]


def generar_hora_realista(intencion: str) -> int:
    if intencion == "SPAM":
        return random.choice([9, 10, 11, 14, 15, 16, 20, 22, 2, 3])
    if random.random() < 0.44:
        return random.choice([18, 19, 20, 21, 22, 23, 0, 6, 7])
    return random.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17])


def generar_dataset(num_filas: int = 520) -> list[dict]:
    random.seed(SEED)
    registros = []
    fecha_base = datetime(2026, 8, 1, 8, 0, 0)

    # 1. Incorporar primero los 30 registros reales orgánicos (origen = 'real')
    for idx_r, (txt_r, int_r, prod_r, monto_r, pago_r, est_r, hora_r, fuera_r, conf_r) in enumerate(REGISTROS_REALES_BITACORA_30):
        ts_msg = fecha_base.replace(hour=hora_r, minute=(idx_r * 7) % 60, second=(idx_r * 13) % 60) + timedelta(days=60 + (idx_r % 15))
        ts_resp = ts_msg + timedelta(seconds=random.randint(2, 15))
        registros.append({
            "id_conversacion": str(uuid.UUID(int=random.getrandbits(128), version=4)),
            "origen": "real",
            "timestamp_primer_mensaje": ts_msg.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_respuesta_bot": ts_resp.strftime("%Y-%m-%d %H:%M:%S"),
            "texto_cliente": txt_r,
            "intencion_predicha": int_r,
            "confianza_modelo": conf_r,
            "producto_cotizado": prod_r,
            "monto_total": round(float(monto_r), 2),
            "metodo_pago": pago_r,
            "estado_pedido": est_r,
            "hora_del_dia": int(hora_r),
            "es_fuera_horario": bool(fuera_r),
        })

    # 2. Generar las 490 filas simuladas calibradas (100% rotuladas con origen = 'simulado')
    clases_simuladas = (
        ["COTIZACION"] * 130
        + ["CONSULTA_TECNICA"] * 124
        + ["ESTADO_PEDIDO"] * 121
        + ["SPAM"] * 115
    )
    random.shuffle(clases_simuladas)

    metodos_pago_validos = ["YAPE", "PLIN", "TARJETA", "EFECTIVO", "TRANSFERENCIA"]

    for idx, intencion in enumerate(clases_simuladas):
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

        dias_offset = random.randint(0, 74)
        minuto = random.randint(0, 59)
        segundo = random.randint(0, 59)
        ts_mensaje = fecha_base.replace(hour=hora, minute=minuto, second=segundo) + timedelta(days=dias_offset)

        segundos_respuesta = random.randint(4, 95) if random.random() < 0.96 else random.randint(120, 480)
        ts_respuesta = ts_mensaje + timedelta(seconds=segundos_respuesta)

        num_ped = random.randint(1040, 9890)
        cantidad = random.choices([1, 2, 3, 4], weights=[0.65, 0.20, 0.10, 0.05])[0]
        monto = min(round(prod_precio * cantidad, 2), 980.00)

        if random.random() < 0.14:
            plantilla_amb, clase_primaria, clase_secundaria = random.choice(CASOS_FRONTERA_AMBIGUOS)
            texto = plantilla_amb.format(prod_corto=prod_corto, monto=f"{monto:.2f}", num_ped=num_ped)
            if random.random() < 0.65:
                intencion = clase_primaria
            else:
                intencion = clase_secundaria
                if random.random() < 0.85:
                    if intencion == "COTIZACION":
                        texto += ", confírmame stock inmediato para pagarlo ahorita"
                    elif intencion == "CONSULTA_TECNICA":
                        texto += ", necesito verificar el calce técnico y milímetros antes de desarmar"
                    elif intencion == "ESTADO_PEDIDO":
                        texto += ", revisa mi comprobante de operación pagado para el despacho"
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

        # Cero celdas vacías: valores explícitos de dominio para cada clase
        if intencion == "SPAM":
            producto_campo = "SIN_PRODUCTO"
            monto_campo = 0.00
            metodo_pago_campo = "NINGUNO"
            estado_pedido_campo = "SIN_PEDIDO"
        elif intencion == "CONSULTA_TECNICA":
            producto_campo = prod_nombre
            monto_campo = round(prod_precio, 2) if random.random() < 0.45 else 0.00
            metodo_pago_campo = "NINGUNO"
            estado_pedido_campo = "SIN_PEDIDO" if random.random() < 0.75 else "COTIZADO"
        elif intencion == "COTIZACION":
            producto_campo = prod_nombre
            monto_campo = monto
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

        # Garantizar que ningún texto contenga números de 9 dígitos (PII / teléfonos)
        texto = re.sub(r"\b\d{9}\b", "canal-digital", texto)

        registros.append(
            {
                "id_conversacion": str(uuid.UUID(int=random.getrandbits(128), version=4)),
                "origen": "simulado",
                "timestamp_primer_mensaje": ts_mensaje.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_respuesta_bot": ts_respuesta.strftime("%Y-%m-%d %H:%M:%S"),
                "texto_cliente": texto,
                "intencion_predicha": intencion,
                "confianza_modelo": confianza,
                "producto_cotizado": producto_campo,
                "monto_total": round(float(monto_campo), 2),
                "metodo_pago": metodo_pago_campo,
                "estado_pedido": estado_pedido_campo,
                "hora_del_dia": int(hora),
                "es_fuera_horario": bool(es_fuera_horario),
            }
        )

    return registros


def main():
    output_path = Path(__file__).parent / "data" / "dataset_hurios_rally_500.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filas = generar_dataset(520)
    columnas = [
        "id_conversacion",
        "origen",
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
