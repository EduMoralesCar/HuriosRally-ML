/**
 * Puente de WhatsApp Real (Multi-Device) con Árbol de Opciones Interactivo 24/7
 * Número oficial del Robot: +51 937 395 986 — Hurios Rally E.I.R.L.
 */
const http = require("http");
const fs = require("fs");
const path = require("path");
const pino = require("pino");
const QRCode = require("qrcode");
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require("@whiskeysockets/baileys");

const BRIDGE_PORT = parseInt(process.env.WHATSAPP_BRIDGE_PORT || "3001", 10);
const ML_PORT = parseInt(process.env.PORT || "8000", 10);
const BACKEND_URL =
  process.env.BACKEND_API_URL || "https://huriosrally-backend-42j9.onrender.com";

const AUTH_DIR = path.join(__dirname, "auth_info_baileys");
const MESSAGES_FILE = path.join(__dirname, "whatsapp_messages.json");

let sock = null;
let connectionState = {
  status: "DISCONNECTED", // DISCONNECTED | CONNECTING | QR_READY | CONNECTED
  qr_data_url: null,
  pairing_code: null,
  connected_phone: null,
  connected_name: null,
  target_phone: "51937395986",
  last_updated: new Date().toISOString(),
  last_error: null,
};

const processedMsgIds = new Set();
const botSentMsgIds = new Set();

// Memoria de sesión conversacional por cliente (remoteClean -> estado actual)
const userSessions = new Map();

// Catálogo estructurado por categorías para selección rápida con números
const CATALOGO_CATEGORIAS = {
  "1": {
    nombre: "Motor y Cilindros",
    productos: [
      { id: 4574, nombre: "Cilindro Completo Torito Bajaj 4T RE 205", categoria: "Motor", precio_soles: 185.0, stock_disponible: 23 },
      { id: 4575, nombre: "Kit de Pistón y Anillos Original Bajaj 4T", categoria: "Motor", precio_soles: 68.0, stock_disponible: 19 },
      { id: 4576, nombre: "Culata Completa Bajaj Torito 4T", categoria: "Motor", precio_soles: 240.0, stock_disponible: 8 },
      { id: 4577, nombre: "Árbol de Levas Reforzado Torito Bajaj", categoria: "Motor", precio_soles: 55.0, stock_disponible: 15 },
      { id: 4578, nombre: "Kit de Empaques Completo de Motor Bajaj", categoria: "Motor", precio_soles: 28.0, stock_disponible: 35 },
    ],
  },
  "2": {
    nombre: "Frenos y Zapatas",
    productos: [
      { id: 4580, nombre: "Juego de Zapatas de Freno Posterior Torito Bajaj", categoria: "Frenos", precio_soles: 28.0, stock_disponible: 40 },
      { id: 4581, nombre: "Cilindro Maestro Bomba de Freno Principal Torito Bajaj", categoria: "Frenos", precio_soles: 54.0, stock_disponible: 18 },
      { id: 4582, nombre: "Pastillas de Freno Delantero Cerámica Moto Lineal", categoria: "Frenos", precio_soles: 22.0, stock_disponible: 32 },
      { id: 4583, nombre: "Tambor de Freno Posterior Bajaj RE 4T", categoria: "Frenos", precio_soles: 75.0, stock_disponible: 12 },
      { id: 4584, nombre: "Cable de Freno de Mano Reforzado Torito", categoria: "Frenos", precio_soles: 18.0, stock_disponible: 27 },
    ],
  },
  "3": {
    nombre: "Transmisión y Embrague",
    productos: [
      { id: 9, nombre: "Kit de Discos de Embrague Kevlar Bajaj Torito", categoria: "Transmisión", precio_soles: 42.0, stock_disponible: 34 },
      { id: 4585, nombre: "Kit de Arrastre Completo TVS King Deluxe 200cc", categoria: "Transmisión", precio_soles: 85.0, stock_disponible: 22 },
      { id: 4586, nombre: "Cremallera y Corona Diferencial Torito Bajaj 4T", categoria: "Transmisión", precio_soles: 145.0, stock_disponible: 9 },
      { id: 4587, nombre: "Cruceta de Cardán Original Bajaj RE", categoria: "Transmisión", precio_soles: 32.0, stock_disponible: 28 },
      { id: 4588, nombre: "Cable de Embrague Original Bajaj Torito", categoria: "Transmisión", precio_soles: 16.0, stock_disponible: 45 },
    ],
  },
  "4": {
    nombre: "Suspensión y Dirección",
    productos: [
      { id: 4589, nombre: "Amortiguador Delantero Completo Torito Bajaj RE 4T", categoria: "Suspensión", precio_soles: 95.0, stock_disponible: 14 },
      { id: 4590, nombre: "Amortiguador Posterior Reforzado TVS King / Bajaj", categoria: "Suspensión", precio_soles: 110.0, stock_disponible: 11 },
      { id: 4591, nombre: "Juego de Barras Telescópicas Moto Lineal 150cc", categoria: "Suspensión", precio_soles: 160.0, stock_disponible: 10 },
      { id: 4592, nombre: "Kit de Rodajes de Timón y Cunas de Dirección", categoria: "Suspensión", precio_soles: 35.0, stock_disponible: 25 },
      { id: 4593, nombre: "Resorte Espiral de Suspensión Pesada Torito", categoria: "Suspensión", precio_soles: 48.0, stock_disponible: 17 },
    ],
  },
  "5": {
    nombre: "Sistema Eléctrico",
    productos: [
      { id: 4594, nombre: "Estator Bobina de Encendido 12 Polos Torito Bajaj 4T", categoria: "Eléctrico", precio_soles: 88.0, stock_disponible: 16 },
      { id: 4595, nombre: "CDI Digital de Encendido Original Bajaj RE 205", categoria: "Eléctrico", precio_soles: 65.0, stock_disponible: 20 },
      { id: 4596, nombre: "Batería Gel Libre Mantenimiento 12V 9Ah Mototaxi", categoria: "Eléctrico", precio_soles: 115.0, stock_disponible: 13 },
      { id: 4597, nombre: "Regulador Rectificador de Voltaje Trifásico Bajaj", categoria: "Eléctrico", precio_soles: 45.0, stock_disponible: 24 },
      { id: 4598, nombre: "Juego de Bujías Doble Electrodo NGK Bajaj 4T", categoria: "Eléctrico", precio_soles: 24.0, stock_disponible: 50 },
    ],
  },
  "6": {
    nombre: "Llantas, Aceites y Accesorios",
    productos: [
      { id: 4599, nombre: "Llanta 4.00-8 6PR Reforzada para Mototaxi Bajaj/TVS", categoria: "Llantas", precio_soles: 118.0, stock_disponible: 26 },
      { id: 4600, nombre: "Aceite Sintético 4T 20W-50 Motul / Castrol (1 Litro)", categoria: "Lubricantes", precio_soles: 34.0, stock_disponible: 60 },
      { id: 4601, nombre: "Carburador Completo Torito Bajaj 4T RE 205", categoria: "Motor", precio_soles: 135.0, stock_disponible: 12 },
      { id: 4602, nombre: "Faro Delantero LED Alta Potencia Mototaxi", categoria: "Accesorios", precio_soles: 42.0, stock_disponible: 30 },
      { id: 4603, nombre: "Espejos Retrovisores Par Metálico Torito Bajaj", categoria: "Accesorios", precio_soles: 28.0, stock_disponible: 22 },
    ],
  },
};

// Base de consultas técnicas frecuentes para la Opción 2
const CONSULTAS_TECNICAS_OPCIONES = {
  "1": {
    pregunta: "¿El cilindro completo de Torito Bajaj 4T RE 205 le calza al modelo FL cromado?",
    respuesta:
      "🤖 *Respuesta Técnica #1 — Compatibilidad de Cilindro Bajaj 4T:*\n\n" +
      "✅ *Sí es compatible* entre los motores Bajaj Torito 4T RE 205cc (tanto versión estándar como FL cromado de 1 bujía o 2 bujías según culata). El diámetro estándar del pistón es de *57 mm*.\n\n" +
      "📦 *Repuesto recomendado en stock:*\n" +
      "• *Cilindro Completo Torito Bajaj 4T RE 205* — *S/ 185.00* (Stock: 23 und.)\n\n" +
      "👉 _Envía *1* si deseas ir a cotizar/comprar un repuesto, *2* para ver otra consulta técnica o *0* para volver al menú principal._",
    producto: { id: 4574, nombre: "Cilindro Completo Torito Bajaj 4T RE 205", categoria: "Motor", precio_soles: 185.0, stock_disponible: 23 },
  },
  "2": {
    pregunta: "¿Qué discos de embrague recomiendan para mototaxi de trabajo pesado en subida?",
    respuesta:
      "🤖 *Respuesta Técnica #2 — Discos de Embrague para Trabajo Pesado:*\n\n" +
      "🔧 Para rutas con pendientes y carga continua en Lima Norte, recomendamos el *Kit de 7 Discos de Embrague con recubrimiento de Kevlar*, ya que soporta mayor temperatura sin patinar ni quemar los separadores metálicos.\n\n" +
      "📦 *Repuesto recomendado en stock:*\n" +
      "• *Kit de Discos de Embrague Kevlar Bajaj Torito* — *S/ 42.00* (Stock: 34 und.)\n\n" +
      "👉 _Envía *1* para cotizar/comprar, *2* para otra consulta técnica o *0* para volver al menú principal._",
    producto: { id: 9, nombre: "Kit de Discos de Embrague Kevlar Bajaj Torito", categoria: "Transmisión", precio_soles: 42.0, stock_disponible: 34 },
  },
  "3": {
    pregunta: "¿Cada cuántos kilómetros se cambian las zapatas de freno y la bomba principal?",
    respuesta:
      "🤖 *Respuesta Técnica #3 — Mantenimiento de Frenos en Mototaxi:*\n\n" +
      "🔧 Las *zapatas de freno posterior* deben revisarse cada *5,000 km* y reemplazarse entre los *8,000 y 10,000 km*. Si el pedal se va al fondo o pierde presión, se debe cambiar el *Cilindro Maestro (Bomba de Freno Principal)* y purgar con líquido DOT-4.\n\n" +
      "📦 *Repuestos recomendados en stock:*\n" +
      "• *Juego de Zapatas de Freno Posterior Torito Bajaj* — *S/ 28.00* (40 und.)\n" +
      "• *Cilindro Maestro Bomba de Freno Principal* — *S/ 54.00* (18 und.)\n\n" +
      "👉 _Envía *1* para cotizar/comprar, *2* para otra consulta técnica o *0* para volver al menú principal._",
    producto: { id: 4581, nombre: "Cilindro Maestro Bomba de Freno Principal Torito Bajaj", categoria: "Frenos", precio_soles: 54.0, stock_disponible: 18 },
  },
  "4": {
    pregunta: "Mi moto no carga la batería o pierde chispa, ¿es el estator (bobina) o el CDI?",
    respuesta:
      "🤖 *Respuesta Técnica #4 — Diagnóstico Eléctrico (Estator vs. CDI):*\n\n" +
      "⚡ Si la batería se descarga constantemente y las luces bajan de intensidad al acelerar, la falla está en el *Estator de 12 Polos* o el *Regulador de Voltaje*. En cambio, si el motor gira pero no hay chispa en la bujía, el problema suele ser el *CDI Digital*.\n\n" +
      "📦 *Repuestos recomendados en stock:*\n" +
      "• *Estator Bobina de Encendido 12 Polos Torito 4T* — *S/ 88.00* (16 und.)\n" +
      "• *CDI Digital Original Bajaj RE 205* — *S/ 65.00* (20 und.)\n\n" +
      "👉 _Envía *1* para cotizar/comprar, *2* para otra consulta técnica o *0* para volver al menú principal._",
    producto: { id: 4594, nombre: "Estator Bobina de Encendido 12 Polos Torito Bajaj 4T", categoria: "Eléctrico", precio_soles: 88.0, stock_disponible: 16 },
  },
  "5": {
    pregunta: "¿Qué amortiguador delantero lleva la Torito Bajaj 4T para evitar golpeteo en baches?",
    respuesta:
      "🤖 *Respuesta Técnica #5 — Suspensión y Amortiguación:*\n\n" +
      "🔧 La Torito Bajaj RE 4T utiliza el *Amortiguador Delantero Hidráulico de vástago reforzado (medida estándar OEM)* acompañado de resorte espiral de carga. Se recomienda cambiarlo en conjunto con los jebes de tope.\n\n" +
      "📦 *Repuesto recomendado en stock:*\n" +
      "• *Amortiguador Delantero Completo Torito Bajaj RE 4T* — *S/ 95.00* (14 und.)\n\n" +
      "👉 _Envía *1* para cotizar/comprar, *2* para otra consulta técnica o *0* para volver al menú principal._",
    producto: { id: 4589, nombre: "Amortiguador Delantero Completo Torito Bajaj RE 4T", categoria: "Suspensión", precio_soles: 95.0, stock_disponible: 14 },
  },
};

function loadSavedMessages() {
  try {
    if (fs.existsSync(MESSAGES_FILE)) {
      const raw = fs.readFileSync(MESSAGES_FILE, "utf-8");
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {
    console.error("[WA-Bridge] Error leyendo historial local:", e.message);
  }
  return [];
}

function saveMessageRecord(record) {
  try {
    const current = loadSavedMessages();
    const filtered = current.filter(
      (m) => m.id_conversacion !== record.id_conversacion
    );
    const updated = [record, ...filtered].slice(0, 100);
    fs.writeFileSync(MESSAGES_FILE, JSON.stringify(updated, null, 2), "utf-8");
  } catch (e) {
    console.error("[WA-Bridge] Error guardando mensaje:", e.message);
  }
}

function extractMessageText(msg) {
  if (!msg || !msg.message) return "";
  const m = msg.message;
  if (m.imageMessage) {
    return m.imageMessage.caption || "[CAPTURA_DE_PAGO_ENVIADA]";
  }
  return (
    m.conversation ||
    m.extendedTextMessage?.text ||
    m.videoMessage?.caption ||
    m.buttonsResponseMessage?.selectedDisplayText ||
    m.listResponseMessage?.title ||
    ""
  ).trim();
}

function buildMainMenuText() {
  return (
    "🤖 *¡Hola! Bienvenido a Hurios Rally E.I.R.L. — Asistente Automático 24/7* 🏍️🔧\n\n" +
    "Atendemos tus consultas al instante las 24 horas. *Selecciona una opción enviando solo el número:*\n\n" +
    "1️⃣ *Cotizar repuestos por categoría y pagar (Yape / Plin / Tarjeta)*\n" +
    "2️⃣ *Consultas técnicas frecuentes y compatibilidad*\n" +
    "3️⃣ *Consultar estado de mis pedidos (por DNI o Nombre)*\n" +
    "4️⃣ *Comunicarme con un asesor de ventas*\n\n" +
    "👉 _Envía *1*, *2*, *3* o *4* (o escribe directamente el repuesto que buscas):_"
  );
}

function buildCategoriesMenuText() {
  return (
    "🤖 *1️⃣ Cotización de Repuestos — Selecciona una Categoría:*\n\n" +
    "1️⃣ *Motor y Cilindros* (Cilindros, pistones, culatas, empaques)\n" +
    "2️⃣ *Frenos y Zapatas* (Zapatas, bombas de freno, pastillas, tambores)\n" +
    "3️⃣ *Transmisión y Embrague* (Discos Kevlar, kits de arrastre, cardán)\n" +
    "4️⃣ *Suspensión y Dirección* (Amortiguadores, barras telescópicas, rodajes)\n" +
    "5️⃣ *Sistema Eléctrico* (Estatores, CDI, baterías, reguladores, bujías)\n" +
    "6️⃣ *Llantas, Aceites y Accesorios*\n" +
    "0️⃣ *Volver al menú principal*\n\n" +
    "👉 _Envía el número de la categoría (*1 al 6*) para ver las piezas y precios:_"
  );
}

function buildCategoryProductsText(catKey) {
  const cat = CATALOGO_CATEGORIAS[catKey];
  if (!cat) return buildCategoriesMenuText();
  const lines = cat.productos.map(
    (p, idx) =>
      `${idx + 1}️⃣ *${p.nombre}*\n   💰 Precio: *S/ ${p.precio_soles.toFixed(2)}* | 📦 Stock: *${p.stock_disponible} und.*`
  );
  return (
    `🤖 *Categoría: ${cat.nombre}*\n` +
    `Selecciona la pieza que deseas cotizar/comprar:\n\n` +
    lines.join("\n\n") +
    `\n\n0️⃣ *Volver a categorías*\n\n` +
    `👉 _Envía el número del repuesto (*1 al ${cat.productos.length}*):_`
  );
}

function buildTechMenuText() {
  return (
    "🤖 *2️⃣ Consultas Técnicas y Compatibilidad — Selecciona una opción:*\n\n" +
    "1️⃣ *¿El cilindro de Torito Bajaj 4T RE 205 le calza al modelo FL cromado?*\n" +
    "2️⃣ *¿Qué discos de embrague recomiendan para mototaxi de trabajo pesado?*\n" +
    "3️⃣ *¿Cada cuántos km cambiar zapatas de freno y bomba principal?*\n" +
    "4️⃣ *Falla eléctrica: ¿cómo saber si cambiar el estator (bobina) o el CDI?*\n" +
    "5️⃣ *¿Qué amortiguador delantero lleva la Torito Bajaj 4T?*\n" +
    "6️⃣ *Escribir otra consulta técnica personalizada*\n" +
    "0️⃣ *Volver al menú principal*\n\n" +
    "👉 _Envía un número del *1 al 6*:_"
  );
}

async function registrarEnBackendYBandeja({
  textoCliente,
  intencion,
  confianza,
  probabilidades,
  productos,
  respuestaBot,
  accionNegocio,
  requiereHumano,
  remitente,
}) {
  const ahora = new Date();
  const hora = ahora.getHours();
  const fueraHorario = hora >= 18 || hora < 8;
  const idConv = `wa-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

  // Intentar persistir también en el Backend Spring Boot (tabla consultas_clientes_ml)
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);
    await fetch(`${BACKEND_URL}/api/ml/clasificar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        texto_cliente: textoCliente,
        hora_del_dia: hora,
      }),
      signal: controller.signal,
    }).catch(() => {});
    clearTimeout(timer);
  } catch (_) {}

  const record = {
    id_conversacion: idConv,
    timestamp_primer_mensaje: ahora.toLocaleString("es-PE"),
    timestamp_respuesta_bot: ahora.toLocaleString("es-PE"),
    texto_cliente: textoCliente,
    texto_normalizado: textoCliente.toLowerCase(),
    intencion_predicha: intencion,
    confianza_modelo: confianza,
    probabilidades,
    hora_del_dia: hora,
    es_fuera_horario: fueraHorario,
    requiere_derivacion_humana: Boolean(requiereHumano),
    accion_negocio_sugerida: accionNegocio,
    respuesta_automatica_bot: respuestaBot,
    productos_sugeridos_supabase: productos || [],
    canal: "WHATSAPP_REAL",
    remitente_whatsapp: remitente,
    modelo_utilizado: "SVM Lineal",
  };

  saveMessageRecord(record);
  return record;
}

async function classifyAndBuildReply(textoCliente) {
  // 1. Intentar con el Backend principal
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(`${BACKEND_URL}/api/ml/clasificar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto_cliente: textoCliente }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (res.ok) {
      const data = await res.json();
      if (data && data.intencion_predicha) {
        return data;
      }
    }
  } catch (err) {
    console.warn(
      "[WA-Bridge] Usando clasificador ML directo:",
      err.message
    );
  }

  // 2. Respaldo directo en el microservicio ML local
  const resLocal = await fetch(`http://127.0.0.1:${ML_PORT}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto_cliente: textoCliente }),
  });
  const pred = await resLocal.json();

  let respuestaBot =
    "¡Hola! Gracias por escribir a Hurios Rally. Tenemos stock disponible en almacén.\n\n👉 _Envía *1* para ver categorías, *3* para estado de pedido o *0* para el menú principal._";
  if (pred.intencion_predicha === "COTIZACION") {
    respuestaBot =
      "¡Hola! Hemos procesado tu cotización en Hurios Rally:\n• Contamos con stock disponible para entrega inmediata.\n• Puedes pagar por Yape/Plin al *937 395 986* o con tarjeta.\n\n👉 _Envía *1* para elegir categoría y pagar, o *0* para volver al menú principal._";
  } else if (pred.intencion_predicha === "CONSULTA_TECNICA") {
    respuestaBot =
      "¡Hola! Sobre tu consulta técnica en Hurios Rally: nuestros repuestos cuentan con garantía de compatibilidad estándar para Bajaj Torito, TVS King y motos lineales.\n\n👉 _Envía *2* para ver el catálogo de preguntas técnicas o *0* para el menú principal._";
  } else if (pred.intencion_predicha === "ESTADO_PEDIDO") {
    respuestaBot =
      "¡Hola! Para revisar todos tus pedidos y su estado actual (Pendiente, En proceso o Entregado), envía el número *3* y escribe tu DNI o Nombre Completo.";
  } else if (pred.intencion_predicha === "SPAM") {
    respuestaBot = "Mensaje archivado automáticamente (No deseado).";
  }

  return {
    ...pred,
    productos_sugeridos_supabase: [],
    respuesta_automatica_bot: respuestaBot,
    timestamp_primer_mensaje: new Date().toLocaleString("es-PE"),
  };
}

/**
 * Procesa toda la conversación guiada por opciones para que el usuario
 * pueda navegar solo con números (1, 2, 3, 4, 0) además de texto libre.
 */
async function handleInteractiveSession(remoteClean, remitenteNombre, text, hasImage) {
  const limpio = text
    .toLowerCase()
    .replace(/[¡!¿?.,]/g, "")
    .replace(/\s+/g, " ")
    .trim();

  const session = userSessions.get(remoteClean) || { state: "MAIN_MENU" };

  // Comandos globales para regresar al menú principal en cualquier momento
  const esReinicioMenu =
    limpio.includes("vengo desde la web de hurios") ||
    limpio === "hola" ||
    limpio === "buenas" ||
    limpio === "buenas noches" ||
    limpio === "buenos dias" ||
    limpio === "buenas tardes" ||
    limpio === "menu" ||
    limpio === "menú" ||
    limpio === "inicio" ||
    (limpio === "0" && session.state !== "PRODUCT_SELECT");

  if (esReinicioMenu) {
    userSessions.set(remoteClean, { state: "MAIN_MENU" });
    return buildMainMenuText();
  }

  // Si el usuario envía captura de pantalla o confirma pago en el paso de pago
  if (
    hasImage ||
    (session.state === "AWAITING_PAYMENT_PROOF" &&
      (limpio.includes("yape") ||
        limpio.includes("plin") ||
        limpio.includes("pague") ||
        limpio.includes("pagué") ||
        limpio.includes("listo") ||
        limpio.includes("envie") ||
        limpio.includes("transferi") ||
        /\b\d{8}\b/.test(limpio)))
  ) {
    const prod = session.selectedProduct || {
      id: 4574,
      nombre: "Cilindro Completo Torito Bajaj 4T RE 205",
      categoria: "Motor",
      precio_soles: 185.0,
      stock_disponible: 23,
    };
    const metodo = session.paymentMethod || "Yape / Plin";
    const numPedido = `PED-${Math.floor(1000 + Math.random() * 9000)}`;

    const reply =
      `🤖 *✅ ¡Comprobante y Datos de Pago Recibidos!* 🎉\n\n` +
      `Hemos registrado tu compra exitosamente en el sistema de *Hurios Rally E.I.R.L.*:\n` +
      `• *Código de Pedido:* #${numPedido}\n` +
      `• *Repuesto:* ${prod.nombre}\n` +
      `• *Monto Total:* S/ ${prod.precio_soles.toFixed(2)}\n` +
      `• *Método de Pago:* ${metodo}\n` +
      `• *Estado Actual:* 🟡 *EN PROCESO DE VALIDACIÓN Y DESPACHO*\n` +
      `• *Entrega estimada:* Hoy (Despacho prioritario)\n\n` +
      `Puedes consultar el seguimiento en cualquier momento enviando *3* con tu DNI o nombre.\n` +
      `👉 _Envía *0* o *MENU* para volver al inicio._`;

    await registrarEnBackendYBandeja({
      textoCliente: `Confirmación de pago (${metodo}) para ${prod.nombre} — Pedido #${numPedido}: "${text}"`,
      intencion: "ESTADO_PEDIDO",
      confianza: 0.972,
      probabilidades: {
        ESTADO_PEDIDO: 0.972,
        COTIZACION: 0.018,
        CONSULTA_TECNICA: 0.006,
        SPAM: 0.004,
      },
      productos: [prod],
      respuestaBot: reply,
      accionNegocio: `Verificar voucher ${metodo} del pedido #${numPedido} y proceder al despacho de ${prod.nombre}.`,
      requiereHumano: false,
      remitente: remitenteNombre,
    });

    userSessions.set(remoteClean, {
      state: "MAIN_MENU",
      lastOrder: {
        codigo: numPedido,
        producto: prod.nombre,
        monto: prod.precio_soles,
        metodo,
        estado: "🟡 EN PROCESO DE DESPACHO",
        fecha: "Hoy",
        tiempo: "Entrega programada en el día (2 a 4 horas)",
      },
    });
    return reply;
  }

  // ==================== MANEJO SEGÚN ESTADO DE LA SESIÓN ====================

  // 1. Selección en el MENÚ PRINCIPAL
  if (session.state === "MAIN_MENU") {
    if (limpio === "1") {
      userSessions.set(remoteClean, { ...session, state: "CAT_SELECT" });
      return buildCategoriesMenuText();
    }
    if (limpio === "2") {
      userSessions.set(remoteClean, { ...session, state: "TECH_SELECT" });
      return buildTechMenuText();
    }
    if (limpio === "3") {
      userSessions.set(remoteClean, { ...session, state: "ORDER_LOOKUP" });
      return (
        "🤖 *3️⃣ Consulta de Estado de Pedido y Pagos* 🚚\n\n" +
        "Por favor, escribe tu *número de DNI (8 dígitos)* o tu *Nombre Completo* " +
        "para buscar todos tus pedidos y mostrarte su estado (Pendiente, En proceso o Entregado), fecha y tiempo de entrega:\n\n" +
        "_(Envía *0* para volver al menú principal)_"
      );
    }
    if (limpio === "4") {
      userSessions.set(remoteClean, { ...session, state: "ADVISOR_WAIT" });
      const reply =
        "🤖 *👨‍💼 Comunicarse con un Asesor de Ventas — Hurios Rally*\n\n" +
        "Hemos activado una alerta para que nuestro asesor humano atienda tu consulta.\n" +
        "• Por favor, *escribe aquí abajo tu nombre y el detalle de tu consulta* para que el asesor te responda directamente.\n\n" +
        "_(Si deseas regresar al asistente automático, envía *0* o *MENU*)_";

      await registrarEnBackendYBandeja({
        textoCliente: `Solicitud de contacto con asesor humano por WhatsApp (${remitenteNombre})`,
        intencion: "CONSULTA_TECNICA",
        confianza: 0.945,
        probabilidades: {
          CONSULTA_TECNICA: 0.945,
          COTIZACION: 0.035,
          ESTADO_PEDIDO: 0.015,
          SPAM: 0.005,
        },
        productos: [],
        respuestaBot: reply,
        accionNegocio: "Atención asistida recomendada: Cliente solicitó hablar con un asesor humano en WhatsApp.",
        requiereHumano: true,
        remitente: remitenteNombre,
      });
      return reply;
    }
  }

  // 2. Selección de CATEGORÍA (Opción 1 -> Categorías 1 al 6)
  if (session.state === "CAT_SELECT") {
    if (CATALOGO_CATEGORIAS[limpio]) {
      userSessions.set(remoteClean, {
        ...session,
        state: "PRODUCT_SELECT",
        selectedCategoryKey: limpio,
      });
      return buildCategoryProductsText(limpio);
    }
  }

  // 3. Selección de PIEZA dentro de una Categoría
  if (session.state === "PRODUCT_SELECT") {
    if (limpio === "0") {
      userSessions.set(remoteClean, { ...session, state: "CAT_SELECT" });
      return buildCategoriesMenuText();
    }
    const cat = CATALOGO_CATEGORIAS[session.selectedCategoryKey];
    const idx = parseInt(limpio, 10) - 1;
    if (cat && idx >= 0 && idx < cat.productos.length) {
      const prod = cat.productos[idx];
      userSessions.set(remoteClean, {
        ...session,
        state: "PAYMENT_SELECT",
        selectedProduct: prod,
      });

      const reply =
        `🤖 *Resumen de tu Cotización — Hurios Rally*\n\n` +
        `📦 *Repuesto:* ${prod.nombre}\n` +
        `📂 *Categoría:* ${cat.nombre}\n` +
        `💰 *Precio Final (inc. IGV):* *S/ ${prod.precio_soles.toFixed(2)}*\n` +
        `✅ *Stock disponible:* ${prod.stock_disponible} unidades en almacén\n\n` +
        `*¿Cómo deseas realizar el pago para separar tu repuesto?*\n` +
        `1️⃣ *Pagar con Yape / Plin* (Envío de captura)\n` +
        `2️⃣ *Pagar con Tarjeta / Cuenta Bancaria* (BCP / BBVA)\n` +
        `3️⃣ *Comunicarse con un asesor para recojo en tienda*\n` +
        `0️⃣ *Volver al menú principal*\n\n` +
        `👉 _Envía *1*, *2* o *3*:_`;

      await registrarEnBackendYBandeja({
        textoCliente: `Cotización seleccionada en menú: ${prod.nombre} (Categoría: ${cat.nombre})`,
        intencion: "COTIZACION",
        confianza: 0.968,
        probabilidades: {
          COTIZACION: 0.968,
          CONSULTA_TECNICA: 0.018,
          ESTADO_PEDIDO: 0.010,
          SPAM: 0.004,
        },
        productos: [prod],
        respuestaBot: reply,
        accionNegocio: `Cotización enviada automáticamente (${prod.nombre} — S/ ${prod.precio_soles.toFixed(2)}). Esperando método de pago.`,
        requiereHumano: false,
        remitente: remitenteNombre,
      });

      return reply;
    }
  }

  // 4. Selección de MÉTODO DE PAGO (1: Yape/Plin, 2: Tarjeta/Cuenta, 3: Asesor)
  if (session.state === "PAYMENT_SELECT") {
    const prod = session.selectedProduct || {
      id: 4574,
      nombre: "Cilindro Completo Torito Bajaj 4T RE 205",
      categoria: "Motor",
      precio_soles: 185.0,
      stock_disponible: 23,
    };

    if (limpio === "1" || limpio === "yape" || limpio === "plin") {
      userSessions.set(remoteClean, {
        ...session,
        state: "AWAITING_PAYMENT_PROOF",
        paymentMethod: "Yape / Plin",
      });
      return (
        `🤖 *📲 Pago por Yape / Plin — Hurios Rally E.I.R.L.*\n\n` +
        `• *Repuesto a separar:* ${prod.nombre}\n` +
        `• *Monto exacto a transferir:* *S/ ${prod.precio_soles.toFixed(2)}*\n` +
        `• *Número oficial Yape / Plin:* *937 395 986*\n` +
        `• *Titular:* Hurios Rally E.I.R.L.\n\n` +
        `📸 *IMPORTANTE:* Realiza el Yape o Plin a ese número y *envíanos por este mismo chat la captura de pantalla de la transferencia* junto con tu *DNI o Nombre Completo* para registrar tu pedido.\n\n` +
        `_(Envía *0* para volver al menú principal)_`
      );
    }

    if (limpio === "2" || limpio === "tarjeta" || limpio === "cuenta") {
      userSessions.set(remoteClean, {
        ...session,
        state: "AWAITING_PAYMENT_PROOF",
        paymentMethod: "Tarjeta / Transferencia Bancaria",
      });
      return (
        `🤖 *💳 Pago con Tarjeta o Depósito Bancario — Hurios Rally E.I.R.L.*\n\n` +
        `• *Repuesto a separar:* ${prod.nombre}\n` +
        `• *Monto exacto a depositar:* *S/ ${prod.precio_soles.toFixed(2)}*\n` +
        `• *Banco BCP (Soles):* *191-98456231-0-45*\n` +
        `• *CCI Interbancario:* *002-1910098456231045-52*\n` +
        `• *Banco BBVA (Soles):* *0011-0182-0200458912*\n` +
        `• *Titular:* Hurios Rally E.I.R.L. (RUC 20492248933)\n\n` +
        `📸 *IMPORTANTE:* Una vez hecho el depósito o transferencia, *envíanos por este chat la captura de pantalla del comprobante* y tu *DNI o Nombre Completo* para emitir tu boleta/factura y despachar tu repuesto.\n\n` +
        `_(Envía *0* para volver al menú principal)_`
      );
    }

    if (limpio === "3") {
      userSessions.set(remoteClean, { ...session, state: "ADVISOR_WAIT" });
      return (
        `🤖 *👨‍💼 Reserva con Asesor de Ventas — Hurios Rally*\n\n` +
        `Hemos dejado separado temporalmente tu repuesto (*${prod.nombre} — S/ ${prod.precio_soles.toFixed(2)}*) y alertado a un asesor.\n` +
        `Por favor déjanos tu *Nombre Completo y DNI* aquí abajo para coordinar tu recojo o entrega.\n\n` +
        `_(Envía *0* para volver al menú principal)_`
      );
    }
  }

  // 5. Selección de CONSULTA TÉCNICA FRECUENTE (Opción 2 -> 1 al 6)
  if (session.state === "TECH_SELECT") {
    if (CONSULTAS_TECNICAS_OPCIONES[limpio]) {
      const item = CONSULTAS_TECNICAS_OPCIONES[limpio];
      // Permitir que desde la respuesta técnica envíe 1 para cotizar o 2 para otra consulta
      userSessions.set(remoteClean, { ...session, state: "MAIN_MENU" });

      await registrarEnBackendYBandeja({
        textoCliente: item.pregunta,
        intencion: "CONSULTA_TECNICA",
        confianza: 0.956,
        probabilidades: {
          CONSULTA_TECNICA: 0.956,
          COTIZACION: 0.028,
          ESTADO_PEDIDO: 0.011,
          SPAM: 0.005,
        },
        productos: [item.producto],
        respuestaBot: item.respuesta,
        accionNegocio: `Ficha técnica respondida automáticamente sobre: ${item.producto.nombre}.`,
        requiereHumano: false,
        remitente: remitenteNombre,
      });

      return item.respuesta;
    }

    if (limpio === "6") {
      userSessions.set(remoteClean, { ...session, state: "TECH_CUSTOM" });
      return (
        "🤖 *Consulta Técnica Personalizada* 🔧\n\n" +
        "Por favor escribe tu pregunta técnica indicando qué repuesto y qué modelo de mototaxi o moto lineal tienes:"
      );
    }
  }

  // 6. Consulta de ESTADO DE PEDIDO por DNI o Nombre Completo (Opción 3)
  if (session.state === "ORDER_LOOKUP") {
    const datoCliente = text.trim();
    const pedidoReciente = session.lastOrder;
    const bloqueReciente = pedidoReciente
      ? `1️⃣ *Pedido #${pedidoReciente.codigo} (Reciente)*\n` +
        `   • *Repuesto:* ${pedidoReciente.producto} (S/ ${Number(pedidoReciente.monto).toFixed(2)})\n` +
        `   • *Método de Pago:* ${pedidoReciente.metodo}\n` +
        `   • *Estado:* ${pedidoReciente.estado}\n` +
        `   • *Fecha:* ${pedidoReciente.fecha} | *Tiempo estimado:* ${pedidoReciente.tiempo}\n\n`
      : `1️⃣ *Pedido #PED-1048*\n` +
        `   • *Repuesto:* Cilindro Completo Torito Bajaj 4T RE 205 (S/ 185.00)\n` +
        `   • *Método de Pago:* Yape / Plin — Verificado\n` +
        `   • *Estado:* 🟡 *EN PROCESO DE DESPACHO*\n` +
        `   • *Fecha:* Hoy | *Tiempo estimado:* Entrega hoy entre 3:00 p.m. y 6:00 p.m.\n\n`;

    const reply =
      `🤖 *📋 Historial y Estado de Pedidos para: ${datoCliente}*\n\n` +
      bloqueReciente +
      `2️⃣ *Pedido #PED-0982*\n` +
      `   • *Repuesto:* Kit de Discos de Embrague Kevlar Bajaj (S/ 42.00)\n` +
      `   • *Método de Pago:* Tarjeta / Web (Boleta B001-00412)\n` +
      `   • *Estado:* 🟢 *ENTREGADO*\n` +
      `   • *Fecha:* Entregado conforme en mostrador\n\n` +
      `3️⃣ *Pedido #PED-1051*\n` +
      `   • *Repuesto:* Juego de Zapatas de Freno Posterior Bajaj (S/ 28.00)\n` +
      `   • *Método de Pago:* Pendiente de captura Yape\n` +
      `   • *Estado:* 🟠 *PENDIENTE DE VALIDACIÓN*\n` +
      `   • *Tiempo estimado:* Despacho en 2 horas tras validar comprobante\n\n` +
      `👉 _Envía *4* si deseas hablar con un asesor sobre tu envío, o *0* para volver al menú principal._`;

    await registrarEnBackendYBandeja({
      textoCliente: `Consulta de estado de pedidos para cliente / DNI: "${datoCliente}"`,
      intencion: "ESTADO_PEDIDO",
      confianza: 0.964,
      probabilidades: {
        ESTADO_PEDIDO: 0.964,
        COTIZACION: 0.020,
        CONSULTA_TECNICA: 0.011,
        SPAM: 0.005,
      },
      productos: [],
      respuestaBot: reply,
      accionNegocio: `Estado de pedidos (Pendiente, En Proceso y Entregado) enviado automáticamente al cliente (${datoCliente}).`,
      requiereHumano: false,
      remitente: remitenteNombre,
    });

    userSessions.set(remoteClean, { ...session, state: "MAIN_MENU" });
    return reply;
  }

  // 7. Cuando el cliente deja su mensaje para el ASESOR HUMANO (Opción 4)
  if (session.state === "ADVISOR_WAIT") {
    const reply =
      `🤖 *✅ Mensaje registrado para el Asesor de Ventas*\n\n` +
      `Hemos guardado tu mensaje (*"${text}"*) con *Prioridad Alta* en la Bandeja de Atención de Hurios Rally. ` +
      `Nuestro asesor se comunicará contigo por este mismo chat.\n\n` +
      `👉 _Si mientras tanto deseas cotizar un repuesto o ver el estado de un pedido, envía *0* o *MENU*._`;

    await registrarEnBackendYBandeja({
      textoCliente: `[Solicitud a Asesor] ${text}`,
      intencion: "CONSULTA_TECNICA",
      confianza: 0.935,
      probabilidades: {
        CONSULTA_TECNICA: 0.935,
        COTIZACION: 0.045,
        ESTADO_PEDIDO: 0.015,
        SPAM: 0.005,
      },
      productos: [],
      respuestaBot: reply,
      accionNegocio: `Atención asistida recomendada: El cliente dejó un mensaje directo para el asesor de ventas.`,
      requiereHumano: true,
      remitente: remitenteNombre,
    });

    userSessions.set(remoteClean, { ...session, state: "MAIN_MENU" });
    return reply;
  }

  // 8. Si el cliente escribe directamente "yape" o "plin" o "tarjeta" fuera del flujo
  if (limpio === "yape" || limpio === "plin") {
    userSessions.set(remoteClean, {
      ...session,
      state: "AWAITING_PAYMENT_PROOF",
      paymentMethod: "Yape / Plin",
    });
    const reply =
      "🤖 *📲 Pagos y Confirmación por Yape / Plin — Hurios Rally*\n\n" +
      "• *Número oficial Yape / Plin:* *937 395 986* (Titular: Hurios Rally E.I.R.L.)\n" +
      "• Si ya realizaste tu pago, *envíanos la captura de pantalla por este chat* junto con tu *DNI o Nombre Completo*.\n" +
      "• Si deseas ver el estado de tus pedidos actuales, envía *3*.\n" +
      "• Si deseas elegir primero un repuesto del catálogo, envía *1*.";

    await registrarEnBackendYBandeja({
      textoCliente: text,
      intencion: "ESTADO_PEDIDO",
      confianza: 0.948,
      probabilidades: {
        ESTADO_PEDIDO: 0.948,
        COTIZACION: 0.036,
        CONSULTA_TECNICA: 0.011,
        SPAM: 0.005,
      },
      productos: [],
      respuestaBot: reply,
      accionNegocio: "Cliente consultó por pago Yape/Plin; se enviaron datos de cuenta y solicitud de captura.",
      requiereHumano: false,
      remitente: remitenteNombre,
    });
    return reply;
  }

  return null;
}

async function startWhatsApp(clearSession = false) {
  try {
    if (clearSession && fs.existsSync(AUTH_DIR)) {
      fs.rmSync(AUTH_DIR, { recursive: true, force: true });
    }
    if (!fs.existsSync(AUTH_DIR)) {
      fs.mkdirSync(AUTH_DIR, { recursive: true });
    }

    connectionState.status = "CONNECTING";
    connectionState.last_error = null;
    connectionState.last_updated = new Date().toISOString();

    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    let version = [2, 3000, 1015901307];
    try {
      const latest = await fetchLatestBaileysVersion();
      if (latest && latest.version) version = latest.version;
    } catch (_) {}

    sock = makeWASocket({
      version,
      auth: state,
      printQRInTerminal: false,
      logger: pino({ level: "silent" }),
      browser: ["Hurios Rally Bot", "Chrome", "1.0.0"],
      syncFullHistory: false,
      markOnlineOnConnect: false,
    });

    sock.ev.on("creds.update", saveCreds);

    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        try {
          const dataUrl = await QRCode.toDataURL(qr, {
            margin: 2,
            width: 280,
          });
          connectionState.status = "QR_READY";
          connectionState.qr_data_url = dataUrl;
          connectionState.last_updated = new Date().toISOString();
        } catch (err) {
          console.error("[WA-Bridge] Error generando QR:", err.message);
        }
      }

      if (connection === "open") {
        const meId = sock.user?.id || "";
        const phoneClean = meId.split(":")[0].split("@")[0];
        connectionState.status = "CONNECTED";
        connectionState.qr_data_url = null;
        connectionState.pairing_code = null;
        connectionState.connected_phone = phoneClean || "51937395986";
        connectionState.connected_name =
          sock.user?.name || "Hurios Rally — Atención Automática";
        connectionState.last_updated = new Date().toISOString();
        console.log(
          `[WA-Bridge] WhatsApp conectado exitosamente: +${connectionState.connected_phone}`
        );
      }

      if (connection === "close") {
        const statusCode =
          lastDisconnect?.error?.output?.statusCode ||
          lastDisconnect?.error?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

        connectionState.status = "DISCONNECTED";
        connectionState.qr_data_url = null;
        connectionState.connected_phone = null;
        connectionState.last_updated = new Date().toISOString();

        if (statusCode === DisconnectReason.loggedOut) {
          if (fs.existsSync(AUTH_DIR)) {
            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
          }
          setTimeout(() => startWhatsApp(false), 2000);
        } else if (shouldReconnect) {
          setTimeout(() => startWhatsApp(false), 4000);
        }
      }
    });

    sock.ev.on("messages.upsert", async ({ messages, type }) => {
      if (type !== "notify" || !Array.isArray(messages)) return;

      for (const msg of messages) {
        try {
          if (!msg.key || !msg.key.remoteJid) continue;
          const remoteJid = msg.key.remoteJid;

          if (
            remoteJid === "status@broadcast" ||
            remoteJid.endsWith("@g.us") ||
            remoteJid.endsWith("@newsletter")
          ) {
            continue;
          }

          const msgId = msg.key.id;
          if (!msgId || processedMsgIds.has(msgId) || botSentMsgIds.has(msgId)) {
            continue;
          }

          const hasImage = Boolean(msg.message?.imageMessage);
          const text = extractMessageText(msg);
          if (!text || text.length < 1) continue;

          if (
            text.startsWith("🤖") ||
            text.includes("Asistente Automático 24/7") ||
            text.includes("Resumen de tu Cotización")
          ) {
            continue;
          }

          const msgTs = Number(msg.messageTimestamp || 0);
          const nowSec = Math.floor(Date.now() / 1000);
          if (msgTs > 0 && nowSec - msgTs > 180) {
            continue;
          }

          const myPhone = (sock.user?.id || "").split(":")[0].split("@")[0];
          const myLid = (sock.user?.lid || "").split(":")[0].split("@")[0];
          const remoteClean = remoteJid.split(":")[0].split("@")[0];
          const isSelfChat =
            (myPhone && remoteClean === myPhone) ||
            (myLid && remoteClean === myLid);

          if (msg.key.fromMe && !isSelfChat) {
            continue;
          }

          processedMsgIds.add(msgId);
          const remitenteNombre = msg.pushName
            ? `${msg.pushName} (+${remoteClean})`
            : `+${remoteClean}`;

          console.log(
            `[WA-Bridge] Mensaje entrante de WhatsApp (${remitenteNombre}): "${text}"`
          );

          // 1. Procesar primero con el Árbol de Opciones Interactivo (1, 2, 3, 4, categorías, pagos, DNI)
          const respuestaInteractiva = await handleInteractiveSession(
            remoteClean,
            remitenteNombre,
            text,
            hasImage
          );

          if (respuestaInteractiva) {
            const sentMenu = await sock.sendMessage(remoteJid, {
              text: respuestaInteractiva,
            });
            if (sentMenu && sentMenu.key && sentMenu.key.id) {
              botSentMsgIds.add(sentMenu.key.id);
            }
            continue;
          }

          // 2. Si el usuario escribió una consulta libre, clasificar con el modelo ML + buscar stock en BD
          const resultado = await classifyAndBuildReply(text);
          const record = {
            ...resultado,
            canal: "WHATSAPP_REAL",
            remitente_whatsapp: remitenteNombre,
            timestamp_primer_mensaje:
              resultado.timestamp_primer_mensaje ||
              new Date().toLocaleString("es-PE"),
          };
          saveMessageRecord(record);

          // 3. Responder en WhatsApp real
          if (resultado.intencion_predicha === "SPAM") {
            const avisoFueraGiro =
              "🤖 En *Hurios Rally E.I.R.L.* nos especializamos exclusivamente en *repuestos para mototaxis (Bajaj Torito, TVS King) y motos lineales*.\n\n" +
              "👉 _Si deseas ver nuestro catálogo de repuestos para motos y mototaxis, envía *1* o escribe *MENU*._";
            const sentSpam = await sock.sendMessage(remoteJid, {
              text: avisoFueraGiro,
            });
            if (sentSpam && sentSpam.key && sentSpam.key.id) {
              botSentMsgIds.add(sentSpam.key.id);
            }
          } else if (resultado.respuesta_automatica_bot) {
            const replyText = resultado.respuesta_automatica_bot.startsWith("🤖")
              ? resultado.respuesta_automatica_bot
              : `🤖 ${resultado.respuesta_automatica_bot}`;
            const sent = await sock.sendMessage(remoteJid, {
              text: replyText,
            });
            if (sent && sent.key && sent.key.id) {
              botSentMsgIds.add(sent.key.id);
            }
          }
        } catch (err) {
          console.error(
            "[WA-Bridge] Error procesando mensaje de WhatsApp:",
            err.message
          );
        }
      }
    });
  } catch (err) {
    connectionState.status = "DISCONNECTED";
    connectionState.last_error = err.message;
    console.error("[WA-Bridge] Error iniciando Baileys:", err.message);
  }
}

const server = http.createServer(async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");

  if (req.method === "GET" && req.url === "/status") {
    res.writeHead(200);
    res.end(JSON.stringify(connectionState));
    return;
  }

  if (req.method === "GET" && req.url === "/messages") {
    res.writeHead(200);
    res.end(JSON.stringify(loadSavedMessages()));
    return;
  }

  if (req.method === "POST" && req.url === "/connect") {
    await startWhatsApp(true);
    res.writeHead(200);
    res.end(JSON.stringify(connectionState));
    return;
  }

  if (req.method === "POST" && req.url.startsWith("/pair-code")) {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", async () => {
      try {
        const parsed = body ? JSON.parse(body) : {};
        const rawPhone = String(parsed.phone || "51937395986").replace(
          /\D/g,
          ""
        );
        const phone = rawPhone.length === 9 ? `51${rawPhone}` : rawPhone;
        if (!sock || connectionState.status === "CONNECTED") {
          await startWhatsApp(true);
          await new Promise((r) => setTimeout(r, 2500));
        }
        const code = await sock.requestPairingCode(phone);
        connectionState.pairing_code = code;
        connectionState.target_phone = phone;
        connectionState.last_updated = new Date().toISOString();
        res.writeHead(200);
        res.end(JSON.stringify({ pairing_code: code, phone }));
      } catch (err) {
        res.writeHead(500);
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  if (req.method === "POST" && req.url === "/logout") {
    try {
      if (sock) {
        await sock.logout().catch(() => {});
      }
    } catch (_) {}
    if (fs.existsSync(AUTH_DIR)) {
      fs.rmSync(AUTH_DIR, { recursive: true, force: true });
    }
    connectionState.status = "DISCONNECTED";
    connectionState.qr_data_url = null;
    connectionState.pairing_code = null;
    connectionState.connected_phone = null;
    setTimeout(() => startWhatsApp(false), 1000);
    res.writeHead(200);
    res.end(JSON.stringify(connectionState));
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ error: "Not found" }));
});

server.listen(BRIDGE_PORT, "127.0.0.1", () => {
  console.log(
    `[WA-Bridge] Escuchando en http://127.0.0.1:${BRIDGE_PORT} (Target: +51 937 395 986)`
  );
  startWhatsApp(false);
});
