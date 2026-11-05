/**
 * Puente de WhatsApp Real (Multi-Device) para Hurios Rally (+51 937 395 986)
 * Conecta el número real de WhatsApp con el clasificador ML y el inventario en PostgreSQL.
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
  return (
    m.conversation ||
    m.extendedTextMessage?.text ||
    m.imageMessage?.caption ||
    m.videoMessage?.caption ||
    m.buttonsResponseMessage?.selectedDisplayText ||
    m.listResponseMessage?.title ||
    ""
  ).trim();
}

async function classifyAndBuildReply(textoCliente) {
  // 1. Intentar con el Backend principal (clasifica en ML + busca stock real en PostgreSQL + guarda en BD)
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
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
      "[WA-Bridge] Backend principal en espera, usando clasificador local ML:",
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
    "¡Hola! Gracias por escribir a *Hurios Rally*. Hemos recibido tu consulta y en breve te confirmamos disponibilidad.";
  if (pred.intencion_predicha === "COTIZACION") {
    respuestaBot =
      "¡Hola! Gracias por comunicarte con *Hurios Rally*. Hemos registrado tu solicitud de cotización de repuestos. Aceptamos Yape, Plin y transferencia; en breve te confirmamos el stock exacto y precio.";
  } else if (pred.intencion_predicha === "CONSULTA_TECNICA") {
    respuestaBot =
      "¡Hola! Recibimos tu consulta técnica en *Hurios Rally*. Nuestro especialista verificará las medidas y compatibilidad exacta del repuesto para tu vehículo.";
  } else if (pred.intencion_predicha === "ESTADO_PEDIDO") {
    respuestaBot =
      "¡Hola! Estamos verificando el estado de tu pedido en almacén de *Hurios Rally*. Por favor indícanos tu número de pedido o comprobante para darte el seguimiento exacto.";
  } else if (pred.intencion_predicha === "SPAM") {
    respuestaBot = "Mensaje archivado automáticamente (No deseado).";
  }

  return {
    ...pred,
    productos_sugeridos: [],
    respuesta_automatica_bot: respuestaBot,
    fecha_registro: new Date().toISOString(),
  };
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
    } catch (_) {
      // Usar versión estable por defecto
    }

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

          // Ignorar estados, grupos y canales
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

          const text = extractMessageText(msg);
          if (!text || text.length < 2) continue;

          // Ignorar mensajes enviados por el propio bot
          if (
            text.startsWith("🤖") ||
            text.includes("*Hurios Rally*") ||
            text.includes("Hemos recibido tu consulta")
          ) {
            continue;
          }

          // Verificar antigüedad (solo responder mensajes recientes < 180s)
          const msgTs = Number(msg.messageTimestamp || 0);
          const nowSec = Math.floor(Date.now() / 1000);
          if (msgTs > 0 && nowSec - msgTs > 180) {
            continue;
          }

          // Si fromMe es true, solo permitir si el usuario se escribe a sí mismo para probar
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
          console.log(
            `[WA-Bridge] Mensaje entrante de WhatsApp (${remoteClean}): "${text}"`
          );

          const resultado = await classifyAndBuildReply(text);
          const record = {
            ...resultado,
            canal: "WHATSAPP_REAL",
            remitente_whatsapp: msg.pushName || `+${remoteClean}`,
            fecha_registro:
              resultado.fecha_registro || new Date().toISOString(),
          };
          saveMessageRecord(record);

          // Responder automáticamente en WhatsApp real salvo que sea SPAM
          if (
            resultado.intencion_predicha !== "SPAM" &&
            resultado.respuesta_automatica_bot
          ) {
            const replyText = `🤖 ${resultado.respuesta_automatica_bot}`;
            const sent = await sock.sendMessage(remoteJid, {
              text: replyText,
            });
            if (sent && sent.key && sent.key.id) {
              botSentMsgIds.add(sent.key.id);
            }
            console.log(
              `[WA-Bridge] Respuesta automática enviada en WhatsApp (${resultado.intencion_predicha})`
            );
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

// Servidor HTTP interno para que FastAPI consulte estado, QR, código de vinculación e historial
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
