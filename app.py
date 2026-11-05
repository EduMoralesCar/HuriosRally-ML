"""
Microservicio REST de Clasificación de Intenciones con Machine Learning (FastAPI)
Proyecto: HURIOS RALLY E.I.R.L. (RUC 20492248933) - Avance de Proyecto Final 3 (APF3 - Semana 15)
Se integra mediante HTTP JSON con HuriosRally-backend (Java 17 + Spring Boot) y HuriosRally-Frontend (React).
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

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
    title="Hurios Rally ML - Clasificador de Intenciones API",
    description=(
        "Microservicio de Machine Learning (Scikit-Learn + FastAPI) para clasificar mensajes "
        "de clientes de Hurios Rally E.I.R.L. en 4 intenciones (COTIZACION, CONSULTA_TECNICA, "
        "ESTADO_PEDIDO, SPAM) cumpliendo la Ley N° 29733."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = MODELS_DIR / "modelo_intenciones_hurios.joblib"
METRICS_PATH = MODELS_DIR / "metricas_evaluacion.json"

pipeline_ml = None
metricas_ml = {}


class ConsultaClienteRequest(BaseModel):
    texto_cliente: str = Field(
        ...,
        min_length=2,
        description="Mensaje enviado por el cliente vía WhatsApp o chat web",
        examples=["Hola maestro, ¿tienes kit de cilindro para mi bajajita Torito RE 205 y a cuánto sale?"],
    )
    hora_del_dia: Optional[int] = Field(
        default=None,
        ge=0,
        le=23,
        description="Hora del mensaje (0-23). Si no se envía, toma la hora actual del servidor.",
    )


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


@app.on_event("startup")
def cargar_modelo():
    global pipeline_ml, metricas_ml
    if not MODEL_PATH.exists() or not METRICS_PATH.exists():
        entrenar_modelo()
    pipeline_ml = joblib.load(MODEL_PATH)
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metricas_ml = json.load(f)


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
    prob_dict = { str(c): round(float(p), 4) for c, p in zip(clases_modelo, probs_raw) }
    confianza = round(float(max(probs_raw)), 4)

    # Regla de negocio de Hurios Rally (Paso 4.2 Consigna APF3):
    # Si la confianza es < 0.70 o si es una consulta técnica de compatibilidad compleja, derivar a asesor técnico
    requiere_humano = (confianza < 0.70) or (pred_clase == "CONSULTA_TECNICA" and confianza < 0.85)

    acciones = {
        "COTIZACION": (
            "Consultar stock y precio en tiempo real en Supabase PostgreSQL y enviar cotización "
            "automática con enlace de carrito y pago Yape/Plin."
        ),
        "CONSULTA_TECNICA": (
            "Verificar ficha técnica de compatibilidad Bajaj/TVS/Lineal y, de requerir validación "
            "mecánica fina, escalar al especialista de mostrador en Av. 22 de Agosto 1012, Comas."
        ),
        "ESTADO_PEDIDO": (
            "Consultar tabla de órdenes por código de pedido/Yape en HuriosRally-backend y notificar "
            "estado de despacho o disponibilidad de recojo en tienda."
        ),
        "SPAM": (
            "Filtrar mensaje automáticamente sin consumir tiempo de los vendedores ni generar "
            "alerta en la bandeja de atención."
        ),
    }

    accion_final = acciones.get(pred_clase, "Derivar a bandeja de soporte.")
    if requiere_humano and pred_clase != "SPAM":
        accion_final = f"[ESCALAMIENTO HUMANO PRIORITARIO - Confianza {confianza:.2f}] " + accion_final

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
        modelo_utilizado=metricas_ml.get("modelo_ganador", "SVC"),
    )
