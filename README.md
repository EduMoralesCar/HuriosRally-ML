# HuriosRally-ML — Solución de Machine Learning (APF3 - Semana 15)

Microservicio de **Clasificación Supervisada Multiclase de Intenciones de Clientes** desarrollado para **HURIOS RALLY E.I.R.L. (RUC 20492248933)** como parte del curso **Innovación y Transformación Digital (100000TD09)** — Universidad Tecnológica del Perú (UTP).

## 1. Hilo Conductor del Proyecto
* **APF1 (Semana 5):** Diagnóstico de pérdida de 35%–40% de consultas nocturnas (18:00 a 08:00) y demora de hasta 8 horas en atención por WhatsApp en Av. 22 de Agosto 1012, Comas.
* **APF2 (Semana 10):** Despliegue del MVP Web E-commerce (`HuriosRally-Frontend` en React + `HuriosRally-backend` en Spring Boot Java 17 + PostgreSQL en Supabase con 300 repuestos en 10 categorías) y definición del **Contrato de Datos Preliminar de 12 campos**.
* **APF3 (Semana 15):** Entrenamiento, validación cruzada, optimización de hiperparámetros (`GridSearchCV`) y despliegue del modelo supervisado que clasifica cada mensaje entrante en 4 intenciones de negocio:
  1. `COTIZACION` (stock y precios de repuestos Bajaj/TVS/Lineal)
  2. `CONSULTA_TECNICA` (compatibilidad mecánica y especificaciones)
  3. `ESTADO_PEDIDO` (seguimiento de pagos Yape/Plin, boletas y despacho)
  4. `SPAM` (mensajes irrelevantes o fuera del giro del negocio)

## 2. Estructura del Proyecto
```text
HuriosRally-ML/
├── data/
│   └── dataset_hurios_rally_500.csv       # Dataset de 520 registros con las 12 columnas del Contrato de Datos (APF2)
├── notebooks/
│   └── APF3_Modelo_ML_HuriosRally.ipynb   # Notebook Jupyter documentado (Pasos 1, 2, 3 y 4 de la consigna)
├── models/
│   ├── modelo_intenciones_hurios.joblib   # Pipeline Scikit-Learn ganador exportado
│   └── metricas_evaluacion.json           # Métricas comparativas (Accuracy, Precision, Recall, F1, Matriz de Confusión)
├── reports/
│   └── figures/                           # Gráficos en alta resolución (EDA, Outliers, Comparación, Importancia TF-IDF)
├── generate_dataset.py                    # Generador reproducible del dataset (semilla fija SEED=42)
├── train_pipeline.py                      # Pipeline de entrenamiento, GridSearchCV y evaluación sin Data Leakage
├── app.py                                 # Microservicio FastAPI (POST /predict, GET /model-info, GET /health)
├── requirements.txt                       # Dependencias de Python con versiones fijas
└── Dockerfile                             # Contenedor listo para despliegue en Render
```

## 3. Ejecución Reproducible (Semilla Fija `random_state = 42`)

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2. Generar dataset y entrenar/comparar los 4 modelos (SVM, Regresión Logística, Random Forest, KNN)
.venv\Scripts\python generate_dataset.py
.venv\Scripts\python train_pipeline.py

# 3. Levantar microservicio FastAPI en el puerto 8000
.venv\Scripts\uvicorn app:app --reload --port 8000
```
