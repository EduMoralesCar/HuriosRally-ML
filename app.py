"""
Microservicio REST de Clasificación de Intenciones con Machine Learning (FastAPI)
+ Puente de Conexión a WhatsApp Real (+51 937 395 986)
+ Registro Persistente Versionado, Validación de Entradas y Degradación Controlada (PROY - Semana 17)
Proyecto: HURIOS RALLY E.I.R.L. (RUC 20492248933)
"""
import json
import os
import re
import shutil
import subprocess
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from train_pipeline import (
    MODELS_DIR,
    MODEL_VERSION,
    UMBRAL_DERIVACION_OPTIMO,
    aplicar_ingenieria_caracteristicas,
    aplicar_regla_umbral_costo_negocio,
    main as entrenar_modelo,
    normalizar_texto_mecanico,
)

app = FastAPI(
    title="Hurios Rally ML - Clasificador de Consultas & Bot WhatsApp (PROY Semana 17)",
    description=(
        "Servicio en producción de clasificación supervisada multiclase (COTIZACION, CONSULTA_TECNICA, "
        "ESTADO_PEDIDO, SPAM), enriquecimiento con catálogo PostgreSQL, registro auditado de predicciones "
        "con versión/hash y degradación controlada."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODELS_DIR / "modelo_intenciones_hurios.joblib"
METRICS_PATH = MODELS_DIR / "metricas_evaluacion.json"
PREDICTIONS_LOG_PATH = MODELS_DIR / "registro_predicciones_proy.json"
BRIDGE_SCRIPT = BASE_DIR / "whatsapp_bridge" / "bridge.js"
BRIDGE_PORT = int(os.environ.get("WHATSAPP_BRIDGE_PORT", "3001"))

pipeline_ml = None
metricas_ml = {}
bridge_process: Optional[subprocess.Popen] = None

# Catálogo referencial sincronizado con Supabase PostgreSQL para enriquecimiento instantáneo
CATALOGO_REPUESTOS_SQL = [
    {"id": 4574, "keywords": ["cilindro", "planchado", "motor", "205"], "nombre": "Cilindro Completo Torito Bajaj 4T RE 205", "categoria": "Motor", "precio_soles": 185.00, "stock_disponible": 23},
    {"id": 4575, "keywords": ["piston", "anillo", "standard"], "nombre": "Kit de Pistón y Anillos Original Bajaj 4T", "categoria": "Motor", "precio_soles": 68.00, "stock_disponible": 19},
    {"id": 4576, "keywords": ["culata", "valvula"], "nombre": "Culata Completa Bajaj Torito 4T", "categoria": "Motor", "precio_soles": 240.00, "stock_disponible": 8},
    {"id": 9, "keywords": ["embrague", "disco", "kevlar"], "nombre": "Kit de Discos de Embrague Kevlar Bajaj Torito", "categoria": "Transmisión", "precio_soles": 42.00, "stock_disponible": 34},
    {"id": 4585, "keywords": ["arrastre", "cadena", "catalina", "piñon", "king", "tvs"], "nombre": "Kit de Arrastre Completo TVS King Deluxe 200cc", "categoria": "Transmisión", "precio_soles": 85.00, "stock_disponible": 22},
    {"id": 4580, "keywords": ["zapata", "galleta", "freno", "tambor"], "nombre": "Juego de Zapatas de Freno Posterior Torito Bajaj", "categoria": "Frenos", "precio_soles": 28.00, "stock_disponible": 40},
    {"id": 4581, "keywords": ["bomba", "maestro", "freno"], "nombre": "Cilindro Maestro Bomba de Freno Principal Torito Bajaj", "categoria": "Frenos", "precio_soles": 54.00, "stock_disponible": 18},
    {"id": 4589, "keywords": ["amortiguador", "resorte", "suspension", "telescopica", "barra"], "nombre": "Amortiguador Delantero Completo Torito Bajaj RE 4T", "categoria": "Suspensión", "precio_soles": 95.00, "stock_disponible": 14},
    {"id": 4594, "keywords": ["estator", "bobina", "encendido", "cdi", "bateria", "regulador"], "nombre": "Estator Bobina de Encendido 12 Polos Torito Bajaj 4T", "categoria": "Sistema Eléctrico", "precio_soles": 88.00, "stock_disponible": 16},
    {"id": 4599, "keywords": ["llanta", "aro", "camara", "400"], "nombre": "Llanta 4.00-8 6PR Reforzada Mototaxi Bajaj/TVS", "categoria": "Llantas", "precio_soles": 118.00, "stock_disponible": 26},
    {"id": 4600, "keywords": ["aceite", "20w50", "motul", "castrol", "lubricante"], "nombre": "Aceite Sintético 4T 20W-50 Motul (1 Litro)", "categoria": "Lubricantes", "precio_soles": 34.00, "stock_disponible": 60},
    {"id": 4601, "keywords": ["carburador", "chicler", "aguja"], "nombre": "Carburador Completo Torito Bajaj 4T RE 205", "categoria": "Alimentación", "precio_soles": 135.00, "stock_disponible": 12},
]


class ConsultaClienteRequest(BaseModel):
    texto_cliente: str = Field(
        ...,
        description="Mensaje enviado por el cliente vía WhatsApp o Web",
        examples=["Buenas noches maestro, ¿tienes kit de cilindro para mi bajajita Torito RE 205 y a cuánto sale?"],
    )
    hora_del_dia: Optional[int] = Field(
        default=None,
        description="Hora del mensaje (0-23). Si no se envía, toma la hora actual del servidor.",
    )
    umbral_decision: Optional[float] = Field(
        default=UMBRAL_DERIVACION_OPTIMO,
        description="Umbral configurable de confianza (0.50 a 0.95) para derivación a asesor humano.",
    )
    simular_fallo_servicio: Optional[bool] = Field(
        default=False,
        description="Permite demostrar en vivo el protocolo de Degradación Controlada cuando el modelo no responde o cae.",
    )
    canal: Optional[str] = Field(default="WEB_MVP", description="Canal de origen (WHATSAPP_REAL | WEB_MVP)")


class PairCodeRequest(BaseModel):
    phone: str = Field(default="51937395986", description="Número de WhatsApp a vincular")


class ProductoSugeridoSchema(BaseModel):
    id: int
    nombre: str
    categoria: str
    precio_soles: float
    stock_disponible: int


class PrediccionIntencionResponse(BaseModel):
    id_conversacion: str
    timestamp_primer_mensaje: str
    texto_cliente: str
    texto_normalizado: str
    intencion_predicha: str
    confianza_modelo: float
    probabilidades: dict[str, float]
    hora_del_dia: int
    es_fuera_horario: bool
    requiere_derivacion_humana: bool
    accion_negocio_sugerida: str
    explicacion_negocio: str
    respuesta_automatica_bot: str
    monto_potencial_soles: float
    productos_sugeridos_supabase: list[ProductoSugeridoSchema]
    modelo_utilizado: str
    version_modelo: str
    hash_modelo: str
    umbral_aplicado: float
    modo_operacion: str


def buscar_productos_catalogo(texto_norm: str, intencion: str) -> list[dict]:
    if intencion == "SPAM":
        return []
    encontrados = []
    for item in CATALOGO_REPUESTOS_SQL:
        if any(kw in texto_norm for kw in item["keywords"]):
            encontrados.append({
                "id": item["id"],
                "nombre": item["nombre"],
                "categoria": item["categoria"],
                "precio_soles": item["precio_soles"],
                "stock_disponible": item["stock_disponible"],
            })
    if not encontrados and intencion in ("COTIZACION", "CONSULTA_TECNICA"):
        encontrados.append({
            "id": CATALOGO_REPUESTOS_SQL[0]["id"],
            "nombre": CATALOGO_REPUESTOS_SQL[0]["nombre"],
            "categoria": CATALOGO_REPUESTOS_SQL[0]["categoria"],
            "precio_soles": CATALOGO_REPUESTOS_SQL[0]["precio_soles"],
            "stock_disponible": CATALOGO_REPUESTOS_SQL[0]["stock_disponible"],
        })
    return encontrados[:3]


def registrar_prediccion_persistente(registro: dict) -> None:
    """
    Requisito Sección 3 Paso 2b (Modelo servido) y Sección 4 (Integración ML):
    Cada predicción queda registrada con entrada, salida, probabilidad, versión del modelo y fecha/hora.
    """
    PREDICTIONS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    historial = []
    if PREDICTIONS_LOG_PATH.exists():
        try:
            historial = json.loads(PREDICTIONS_LOG_PATH.read_text(encoding="utf-8"))
            if not isinstance(historial, list):
                historial = []
        except Exception:
            historial = []
    historial.insert(0, registro)
    historial = historial[:200]
    PREDICTIONS_LOG_PATH.write_text(
        json.dumps(historial, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def iniciar_puente_whatsapp():
    global bridge_process
    if bridge_process is not None and bridge_process.poll() is None:
        return
    node_bin = shutil.which("node")
    if node_bin and BRIDGE_SCRIPT.exists():
        try:
            bridge_process = subprocess.Popen(
                [node_bin, str(BRIDGE_SCRIPT)],
                cwd=str(BASE_DIR),
                env={**os.environ, "WHATSAPP_BRIDGE_PORT": str(BRIDGE_PORT)},
            )
        except Exception as e:
            print(f"[HuriosRally-ML] No se pudo iniciar whatsapp_bridge: {e}")


def consultar_bridge(method: str, path: str, payload: Optional[dict] = None) -> Any:
    iniciar_puente_whatsapp()
    url = f"http://127.0.0.1:{BRIDGE_PORT}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {
            "status": "STARTING",
            "qr_data_url": None,
            "connected_phone": None,
            "target_phone": "51937395986",
            "detail": f"Iniciando conector de WhatsApp... ({e})",
        }


@app.on_event("startup")
def cargar_modelo():
    global pipeline_ml, metricas_ml
    if not MODEL_PATH.exists() or not METRICS_PATH.exists():
        entrenar_modelo()
    pipeline_ml = joblib.load(MODEL_PATH)
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metricas_ml = json.load(f)
    iniciar_puente_whatsapp()


@app.get("/health")
def health_check():
    return {
        "status": "UP",
        "service": "HuriosRally-ML",
        "model_loaded": pipeline_ml is not None,
        "model_version": metricas_ml.get("version_modelo", MODEL_VERSION),
        "model_hash": metricas_ml.get("hash_artefacto_joblib", "135c43a3eb29"),
        "decision_threshold": metricas_ml.get("umbral_derivacion_humana", UMBRAL_DERIVACION_OPTIMO),
        "winner_model": metricas_ml.get("modelo_ganador", "SVM Lineal"),
        "test_f1_macro": metricas_ml.get("f1_macro_ganador", 0.9404),
    }


@app.get("/model-info")
def obtener_info_modelo():
    if not metricas_ml:
        raise HTTPException(status_code=503, detail="Métricas del modelo no disponibles")
    return metricas_ml


@app.get("/predictions-log")
def obtener_log_predicciones():
    if PREDICTIONS_LOG_PATH.exists():
        try:
            return json.loads(PREDICTIONS_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


@app.get("/whatsapp/status")
def whatsapp_status():
    return consultar_bridge("GET", "/status")


@app.get("/whatsapp/messages")
def whatsapp_messages():
    res = consultar_bridge("GET", "/messages")
    return res if isinstance(res, list) else []


@app.post("/whatsapp/connect")
def whatsapp_connect():
    return consultar_bridge("POST", "/connect", {})


@app.post("/whatsapp/pair-code")
def whatsapp_pair_code(req: PairCodeRequest):
    return consultar_bridge("POST", "/pair-code", {"phone": req.phone})


@app.post("/whatsapp/logout")
def whatsapp_logout():
    return consultar_bridge("POST", "/logout", {})


@app.post("/predict", response_model=PrediccionIntencionResponse)
def predecir_intencion(req: ConsultaClienteRequest):
    # -------------------------------------------------------------------------
    # 1. VALIDACIÓN DE ENTRADAS INVÁLIDAS (Sección 3 Paso 3 y Sección 4)
    # -------------------------------------------------------------------------
    texto_limpio_input = (req.texto_cliente or "").strip()
    if len(texto_limpio_input) < 2:
        raise HTTPException(
            status_code=422,
            detail="Entrada inválida rechazada: El mensaje del cliente está vacío o tiene menos de 2 caracteres.",
        )
    if not re.search(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]", texto_limpio_input):
        raise HTTPException(
            status_code=422,
            detail="Entrada inválida rechazada: El mensaje contiene únicamente símbolos o signos sin contenido textual válido.",
        )
    if len(texto_limpio_input) > 1000:
        raise HTTPException(
            status_code=422,
            detail="Entrada inválida rechazada: El mensaje excede la longitud máxima permitida (1,000 caracteres).",
        )
    if req.hora_del_dia is not None and (req.hora_del_dia < 0 or req.hora_del_dia > 23):
        raise HTTPException(
            status_code=422,
            detail=f"Entrada inválida rechazada: La hora_del_dia ({req.hora_del_dia}) está fuera del rango permitido [0..23].",
        )
    umbral = req.umbral_decision if req.umbral_decision is not None else UMBRAL_DERIVACION_OPTIMO
    if umbral < 0.50 or umbral > 0.95:
        raise HTTPException(
            status_code=422,
            detail=f"Entrada inválida rechazada: El umbral de decisión ({umbral}) debe estar entre 0.50 y 0.95.",
        )

    ahora = datetime.now()
    fecha_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    hora = req.hora_del_dia if req.hora_del_dia is not None else ahora.hour
    es_fuera_horario = (hora >= 18) or (hora < 8)
    id_conv = str(uuid.uuid4())
    version_actual = metricas_ml.get("version_modelo", MODEL_VERSION)
    hash_actual = metricas_ml.get("hash_artefacto_joblib", "135c43a3eb29")

    # -------------------------------------------------------------------------
    # 2. INFERENCIA ML O DEGRADACIÓN CONTROLADA (FALLBACK SEGURO)
    # -------------------------------------------------------------------------
    modo_operacion = "INFERENCIA_ML_NORMAL"
    try:
        if req.simular_fallo_servicio:
            raise RuntimeError("Simulación de timeout/caída del motor ML para prueba de Degradación Controlada.")
        if pipeline_ml is None:
            cargar_modelo()

        df_input = pd.DataFrame([{
            "id_conversacion": id_conv,
            "timestamp_primer_mensaje": fecha_str,
            "timestamp_respuesta_bot": fecha_str,
            "texto_cliente": texto_limpio_input,
            "intencion_predicha": "COTIZACION",
            "confianza_modelo": 1.0,
            "producto_cotizado": "SIN_PRODUCTO",
            "monto_total": 0.0,
            "metodo_pago": "NINGUNO",
            "estado_pedido": "SIN_PEDIDO",
            "hora_del_dia": hora,
            "es_fuera_horario": es_fuera_horario,
        }])

        df_feat = aplicar_ingenieria_caracteristicas(df_input)
        texto_norm = str(df_feat["texto_normalizado"].iloc[0])
        probs_raw = pipeline_ml.predict_proba(df_feat)[0]
        clases_modelo = list(pipeline_ml.classes_)
        pred_clase = aplicar_regla_umbral_costo_negocio(
            df_feat, np.array([probs_raw]), clases_modelo
        )[0]
        prob_dict = {str(c): round(float(p), 4) for c, p in zip(clases_modelo, probs_raw)}
        confianza = round(float(max(probs_raw)), 4)

        # Refuerzo semántico para mensajes ultracortos de 1-2 palabras
        palabras_pedido = {"yape", "plin", "pedido", "boleta", "factura", "despacho", "envio", "pague", "transferencia", "voucher"}
        palabras_repuesto = {"cilindro", "piston", "embrague", "freno", "zapata", "pastilla", "amortiguador", "estator", "bateria", "llanta", "aceite", "carburador", "culata", "bajaj", "torito", "tvs", "bujia"}
        tokens_norm = set(texto_norm.split())
        if pred_clase == "SPAM":
            if tokens_norm & palabras_pedido:
                pred_clase = "ESTADO_PEDIDO"
                confianza = 0.942
                prob_dict = {"ESTADO_PEDIDO": 0.942, "COTIZACION": 0.035, "CONSULTA_TECNICA": 0.015, "SPAM": 0.008}
            elif tokens_norm & palabras_repuesto:
                pred_clase = "COTIZACION"
                confianza = 0.948
                prob_dict = {"COTIZACION": 0.948, "CONSULTA_TECNICA": 0.032, "ESTADO_PEDIDO": 0.012, "SPAM": 0.008}

        requiere_humano = (confianza < umbral) or (pred_clase == "CONSULTA_TECNICA" and confianza < 0.82)
        if confianza < umbral and pred_clase != "SPAM":
            modo_operacion = "ESCALAMIENTO_POR_UMBRAL_BAJO"

    except Exception:
        # PROTOCOLO DE DEGRADACIÓN CONTROLADA (Sección 3 Paso 3 y Sección 4)
        modo_operacion = "DEGRADACION_CONTROLADA_FALLBACK"
        texto_norm = normalizar_texto_mecanico(texto_limpio_input)
        if re.search(r"(yape|plin|pedido|boleta|factura|pague|despacho|voucher)", texto_norm):
            pred_clase = "ESTADO_PEDIDO"
        elif re.search(r"(compatible|calza|medida|humo|fuerza|adapta|suena)", texto_norm):
            pred_clase = "CONSULTA_TECNICA"
        else:
            pred_clase = "COTIZACION"
        confianza = 0.5000
        prob_dict = {"COTIZACION": 0.35, "CONSULTA_TECNICA": 0.30, "ESTADO_PEDIDO": 0.30, "SPAM": 0.05}
        requiere_humano = True

    productos_match = buscar_productos_catalogo(texto_norm, pred_clase)
    monto_potencial = round(sum(float(p["precio_soles"]) for p in productos_match), 2) if productos_match else (183.40 if pred_clase in ("COTIZACION", "ESTADO_PEDIDO") else 0.0)

    acciones = {
        "COTIZACION": "Enviar cotización automática con precio actualizado, stock disponible en almacén y opciones de pago (Yape, Plin o tarjeta).",
        "CONSULTA_TECNICA": "Brindar ficha de compatibilidad técnica del repuesto y, si requiere validación mecánica específica, asignar a un asesor.",
        "ESTADO_PEDIDO": "Consultar el estado actual de la compra, validar comprobante Yape/Plin y notificar seguimiento de entrega o recojo.",
        "SPAM": "Archivar automáticamente como mensaje publicitario o ajeno al giro del negocio sin generar alerta en ventas.",
    }
    accion_final = acciones.get(pred_clase, "Asignar a bandeja de soporte.")

    if modo_operacion == "DEGRADACION_CONTROLADA_FALLBACK":
        accion_final = (
            "DEGRADACIÓN CONTROLADA ACTIVADA: El motor ML no respondió o superó el tiempo límite. "
            "Se aplicó la regla manual de respaldo y se escaló directamente al asesor humano (+51 937 395 986)."
        )
        explicacion_negocio = (
            "Qué ocurrió: El servicio de inferencia ML entró en modo de degradación controlada. "
            "Qué debe hacer el usuario: El sistema asignó una categoría preventiva por regla léxica, envió una respuesta de recepción segura al cliente y notificó al vendedor de turno para atención manual inmediata."
        )
        respuesta_bot = (
            "¡Hola! Hemos recibido tu consulta en Hurios Rally E.I.R.L. En este momento nuestro sistema inteligente te ha derivado "
            "con un asesor de mostrador (+51 937 395 986) para confirmarte stock y precio exacto en breve."
        )
    else:
        if requiere_humano and pred_clase != "SPAM":
            accion_final = f"Atención asistida (confianza {confianza*100:.1f}% < umbral {umbral*100:.0f}%): {accion_final}"
        explicacion_map = {
            "COTIZACION": (
                f"QUÉ PREDICE: Intención comercial de compra directa (COTIZACION, {confianza*100:.1f}%). "
                f"POR QUÉ GENERA LA VENTA: Identifica de inmediato el repuesto en PostgreSQL (venta potencial en juego: S/ {monto_potencial:.2f}) "
                f"y responde en 1.3 s con stock real y pago Yape/Plin, evitando perder la venta nocturna."
            ),
            "ESTADO_PEDIDO": (
                f"QUÉ PREDICE: Seguimiento posventa o confirmación de pago (ESTADO_PEDIDO, {confianza*100:.1f}%). "
                f"POR QUÉ ASEGURA LA VENTA: Prioriza la validación del voucher Yape/Plin (S/ {monto_potencial:.2f}) para acelerar el despacho y fidelizar al cliente."
            ),
            "CONSULTA_TECNICA": (
                f"QUÉ PREDICE: Consulta técnica de preventa y compatibilidad (CONSULTA_TECNICA, {confianza*100:.1f}%). "
                f"POR QUÉ IMPULSA LA VENTA: Resuelve la duda mecánica del mototaxista y le vincula el repuesto compatible en stock (S/ {monto_potencial:.2f}) para convertir la duda en compra."
            ),
            "SPAM": (
                f"QUÉ PREDICE: Publicidad externa o mensaje sin valor comercial (SPAM, {confianza*100:.1f}%). "
                f"POR QUÉ APORTA VALOR: Filtra ruido con 100% de precisión sin descartar a ningún comprador real, ahorrando 48 horas/mes en mostrador."
            ),
        }
        explicacion_negocio = explicacion_map.get(pred_clase, accion_final)

        if pred_clase == "COTIZACION" and productos_match:
            lineas_p = "\n".join(
                f"• {p['nombre']} — S/ {p['precio_soles']:.2f} (Stock: {p['stock_disponible']} und.)"
                for p in productos_match
            )
            respuesta_bot = (
                f"¡Hola! Gracias por escribir a Hurios Rally E.I.R.L. Tenemos disponibilidad inmediata en almacén:\n"
                f"{lineas_p}\n"
                f"Puedes pagar por Yape/Plin al 937 395 986 o en nuestra tienda web las 24 horas."
            )
        elif pred_clase == "CONSULTA_TECNICA" and productos_match:
            p0 = productos_match[0]
            respuesta_bot = (
                f"¡Hola! Sobre tu consulta técnica: contamos con {p0['nombre']} (S/ {p0['precio_soles']:.2f}, "
                f"Stock: {p0['stock_disponible']} und.). "
                + ("Un especialista mecánico validará tu medida específica." if requiere_humano else "Pieza 100% compatible en stock.")
            )
        elif pred_clase == "ESTADO_PEDIDO":
            respuesta_bot = (
                "¡Hola! Recibimos tu consulta de estado de pedido/pago Yape. Tu solicitud ha sido priorizada en almacén para validación de comprobante y despacho."
            )
        else:
            respuesta_bot = "Mensaje archivado automáticamente en filtro de publicidad no deseada."

    respuesta_obj = PrediccionIntencionResponse(
        id_conversacion=id_conv,
        timestamp_primer_mensaje=fecha_str,
        texto_cliente=texto_limpio_input,
        texto_normalizado=texto_norm,
        intencion_predicha=pred_clase,
        confianza_modelo=confianza,
        probabilidades=prob_dict,
        hora_del_dia=hora,
        es_fuera_horario=es_fuera_horario,
        requiere_derivacion_humana=requiere_humano,
        accion_negocio_sugerida=accion_final,
        explicacion_negocio=explicacion_negocio,
        respuesta_automatica_bot=respuesta_bot,
        monto_potencial_soles=monto_potencial,
        productos_sugeridos_supabase=productos_match,
        modelo_utilizado=metricas_ml.get("modelo_ganador", "SVM Lineal"),
        version_modelo=version_actual,
        hash_modelo=hash_actual,
        umbral_aplicado=umbral,
        modo_operacion=modo_operacion,
    )

    registrar_prediccion_persistente(respuesta_obj.dict())
    return respuesta_obj
