"""
Microservicio REST de Clasificación de Intenciones con Machine Learning (FastAPI)
+ Puente de Conexión a WhatsApp Real (+51 937 395 986)
Proyecto: HURIOS RALLY E.I.R.L.
"""
import json
import os
import shutil
import subprocess
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from train_pipeline import (
    MODELS_DIR,
    aplicar_ingenieria_caracteristicas,
    main as entrenar_modelo,
)

app = FastAPI(
    title="Hurios Rally ML - Clasificador de Consultas & Bot WhatsApp",
    description=(
        "Servicio de clasificación automática de mensajes de clientes "
        "en 4 categorías operativas (COTIZACION, CONSULTA_TECNICA, ESTADO_PEDIDO, SPAM) "
        "y conexión directa con WhatsApp (+51 937 395 986)."
    ),
    version="1.1.0",
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
BRIDGE_SCRIPT = BASE_DIR / "whatsapp_bridge" / "bridge.js"
BRIDGE_PORT = int(os.environ.get("WHATSAPP_BRIDGE_PORT", "3001"))

pipeline_ml = None
metricas_ml = {}
bridge_process: Optional[subprocess.Popen] = None


class ConsultaClienteRequest(BaseModel):
    texto_cliente: str = Field(
        ...,
        min_length=2,
        description="Mensaje enviado por el cliente vía WhatsApp",
        examples=["Hola maestro, ¿tienes kit de cilindro para mi bajajita Torito RE 205 y a cuánto sale?"],
    )
    hora_del_dia: Optional[int] = Field(
        default=None,
        ge=0,
        le=23,
        description="Hora del mensaje (0-23). Si no se envía, toma la hora actual del servidor.",
    )


class PairCodeRequest(BaseModel):
    phone: str = Field(default="51937395986", description="Número de WhatsApp a vincular")


class PrediccionIntencionResponse(BaseModel):
    id_conversacion: str
    texto_cliente: str
    texto_normalizado: str
    intencion_predicha: str
    confianza_modelo: float
    probabilidades: dict[str, float]
    hora_del_dia: int
    es_fuera_horario: bool
    requiere_derivacion_humana: bool
    accion_negocio_sugerida: str
    modelo_utilizado: str


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
        "winner_model": metricas_ml.get("modelo_ganador", "N/A"),
        "test_f1_macro": metricas_ml.get("f1_macro_ganador", 0.0),
    }


@app.get("/model-info")
def obtener_info_modelo():
    if not metricas_ml:
        raise HTTPException(status_code=503, detail="Métricas del modelo no disponibles")
    return metricas_ml


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
    if pipeline_ml is None:
        cargar_modelo()

    ahora = datetime.now()
    hora = req.hora_del_dia if req.hora_del_dia is not None else ahora.hour
    es_fuera_horario = (hora >= 18) or (hora < 8)

    df_input = pd.DataFrame(
        [
            {
                "id_conversacion": str(uuid.uuid4()),
                "timestamp_primer_mensaje": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_respuesta_bot": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                "texto_cliente": req.texto_cliente,
                "intencion_predicha": "COTIZACION",
                "confianza_modelo": 1.0,
                "producto_cotizado": "SIN_PRODUCTO",
                "monto_total": 0.0,
                "metodo_pago": "NINGUNO",
                "estado_pedido": "SIN_PEDIDO",
                "hora_del_dia": hora,
                "es_fuera_horario": es_fuera_horario,
            }
        ]
    )

    df_feat = aplicar_ingenieria_caracteristicas(df_input)
    pred_clase = str(pipeline_ml.predict(df_feat)[0])
    probs_raw = pipeline_ml.predict_proba(df_feat)[0]
    clases_modelo = list(pipeline_ml.classes_)
    prob_dict = {str(c): round(float(p), 4) for c, p in zip(clases_modelo, probs_raw)}
    confianza = round(float(max(probs_raw)), 4)

    requiere_humano = (confianza < 0.70) or (pred_clase == "CONSULTA_TECNICA" and confianza < 0.85)

    acciones = {
        "COTIZACION": (
            "Enviar cotización automática con precio actualizado, stock disponible en almacén "
            "y opciones de pago (Yape, Plin o tarjeta)."
        ),
        "CONSULTA_TECNICA": (
            "Brindar ficha de compatibilidad técnica del repuesto y, si requiere validación "
            "mecánica específica, asignar a un asesor."
        ),
        "ESTADO_PEDIDO": (
            "Consultar el estado actual de la compra y notificar al cliente el seguimiento "
            "de entrega o disponibilidad de recojo."
        ),
        "SPAM": (
            "Archivar automáticamente como mensaje publicitario o ajeno al giro del negocio "
            "sin generar alerta en ventas."
        ),
    }

    accion_final = acciones.get(pred_clase, "Asignar a bandeja de soporte.")
    if requiere_humano and pred_clase != "SPAM":
        accion_final = f"Atención asistida recomendada: {accion_final}"

    return PrediccionIntencionResponse(
        id_conversacion=str(df_input["id_conversacion"].iloc[0]),
        texto_cliente=req.texto_cliente,
        texto_normalizado=str(df_feat["texto_normalizado"].iloc[0]),
        intencion_predicha=pred_clase,
        confianza_modelo=confianza,
        probabilidades=prob_dict,
        hora_del_dia=hora,
        es_fuera_horario=es_fuera_horario,
        requiere_derivacion_humana=requiere_humano,
        accion_negocio_sugerida=accion_final,
        modelo_utilizado=metricas_ml.get("modelo_ganador", "SVM Lineal"),
    )
