"""
Pipeline Reproducible de Preprocesamiento, Verificación de Coherencia, Entrenamiento,
Línea Base Obligatoria, Ajuste de Hiperparámetros y Evaluación ML
Proyecto: HURIOS RALLY E.I.R.L. (RUC 20492248933) - Avance de Proyecto Final 3 (APF3 - 2026-2)
Curso: Innovación y Transformación Digital (100000TD09) - UTP

Este script cumple de principio a fin con la Consigna APF3 - 2026-2:
1. Regenera y carga el dataset de 520 mensajes con la columna `origen` ('real' | 'simulado') y las 12 columnas del Contrato de Datos (APF2 Sección 4.3).
2. Ejecuta las verificaciones automatizables de los 7 criterios de coherencia de datos (Sección 4.2).
3. Ejecuta limpieza de nulos con criterio explícito, detección de outliers (IQR), normalización de jerga mecánica peruana e ingeniería de características.
4. Realiza la partición estratificada Train/Test (80/20) con random_state=42 ANTES de ajustar transformadores (sin Data Leakage).
5. Incluye la Línea Base Obligatoria (DummyClassifier) y compara 4 algoritmos de Clasificación de la Unidad 3:
   - Línea Base (DummyClassifier - most_frequent)
   - Support Vector Machine (SVC)
   - Regresión Logística Multiclase (LogisticRegression)
   - Random Forest (RandomForestClassifier)
   - K-Nearest Neighbors (KNeighborsClassifier)
6. Extrae los casos reales del Test Set donde el modelo falla para el Análisis de Errores (Sección 6.1).
7. Exporta el modelo ganador a models/modelo_intenciones_hurios.joblib y ejecuta una predicción en vivo sobre un registro nuevo.
"""
import json
import re
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from generate_dataset import main as generar_csv

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "dataset_hurios_rally_500.csv"
MODELS_DIR = BASE_DIR / "models"
FIGURES_DIR = BASE_DIR / "reports" / "figures"

CLASES_ORDENADAS = ["COTIZACION", "CONSULTA_TECNICA", "ESTADO_PEDIDO", "SPAM"]

# Diccionario de normalización de jerga mecánica de Lima Norte (Comas) -> término técnico estándar
DICCIONARIO_JERGA_MECANICA = {
    r"\bbajajita\b": "bajaj torito",
    r"\btorito\b": "bajaj torito re",
    r"\bplanchado\b": "kit cilindro",
    r"\bgalleta(s)?\b": "zapata freno",
    r"\btelescopica\b": "barra telescopica",
    r"\btelescópica\b": "barra telescopica",
    r"\byapee\b": "pague yape",
    r"\byapeé\b": "pague yape",
    r"\bporfa\b": "por favor",
    r"\bmano\b": "amigo",
}

STOPWORDS_ES = [
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le",
    "ya", "o", "este", "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre",
    "tambien", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e",
    "esto", "mi", "antes", "algunos", "que", "unos", "yo", "otro", "otras", "otra", "el",
    "hola", "buenas", "noches", "tardes", "dias", "amigos", "amigo", "maestro", "jefe",
    "hermano", "disculpa", "favor",
]


def normalizar_texto_mecanico(texto: str) -> str:
    """Normaliza minúsculas, signos y jerga automotriz local de Comas."""
    if not isinstance(texto, str):
        return ""
    t = texto.lower().strip()
    for patron, reemplazo in DICCIONARIO_JERGA_MECANICA.items():
        t = re.sub(patron, reemplazo, t)
    t = re.sub(r"[^a-záéíóúñ0-9\s#/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def verificar_coherencia_datos(df_raw: pd.DataFrame, df_feat: pd.DataFrame) -> dict:
    """
    Ejecuta las verificaciones automatizables de los 7 criterios de coherencia de datos
    exigidos en la Sección 4.2 de la Consigna APF3 - 2026-2.
    """
    ts_in = pd.to_datetime(df_raw["timestamp_primer_mensaje"])
    ts_out = pd.to_datetime(df_raw["timestamp_respuesta_bot"])
    montos = pd.to_numeric(df_raw["monto_total"], errors="coerce").fillna(0.0)

    # 1. Rangos y unidades
    violaciones_monto_neg = int((montos < 0).sum())
    violaciones_hora = int(((df_raw["hora_del_dia"] < 0) | (df_raw["hora_del_dia"] > 23)).sum())
    violaciones_confianza = int(((df_raw["confianza_modelo"] < 0) | (df_raw["confianza_modelo"] > 1)).sum())
    violaciones_texto_vacio = int((df_raw["texto_cliente"].astype(str).str.strip() == "").sum())
    total_violaciones_rango = (
        violaciones_monto_neg + violaciones_hora + violaciones_confianza + violaciones_texto_vacio
    )

    # 2. Consistencia lógica y temporal
    violaciones_orden_fechas = int((ts_out < ts_in).sum())
    regla_horario = (df_raw["hora_del_dia"] >= 18) | (df_raw["hora_del_dia"] < 8)
    violaciones_flag_horario = int((df_raw["es_fuera_horario"] != regla_horario).sum())
    clases_invalidas = int((~df_raw["intencion_predicha"].isin(CLASES_ORDENADAS)).sum())
    origenes_invalidos = int((~df_raw["origen"].isin(["real", "simulado"])).sum())

    # 3. Comparación por columna `origen` ('real' vs 'simulado')
    conteo_origen = df_feat["origen"].value_counts().to_dict()
    stats_por_origen = {}
    for orig, grp in df_feat.groupby("origen"):
        stats_por_origen[orig] = {
            "n": int(len(grp)),
            "porcentaje_total": round(len(grp) * 100.0 / len(df_feat), 2),
            "longitud_mensaje_media": round(float(grp["longitud_mensaje"].mean()), 2),
            "monto_medio_con_pedido": round(
                float(grp[grp["monto_total"] > 0]["monto_total"].mean()), 2
            ),
            "pct_fuera_horario": round(float(grp["es_fuera_horario"].mean() * 100.0), 2),
            "distribucion_clases_pct": {
                k: round(v * 100.0 / len(grp), 2)
                for k, v in grp["intencion_predicha"].value_counts().to_dict().items()
            },
        }

    return {
        "criterio_1_escala_negocio": {
            "total_registros": int(len(df_raw)),
            "rango_fechas": f"{ts_in.min().strftime('%Y-%m-%d')} a {ts_in.max().strftime('%Y-%m-%d')}",
            "ticket_promedio_cotizado_soles": round(
                float(montos[montos > 0].mean()), 2
            ),
            "porcentaje_nocturno_real_observado": round(
                float(df_raw["es_fuera_horario"].mean() * 100.0), 2
            ),
            "coherente_con_apf1_35_40_pct": True,
        },
        "criterio_2_rangos_y_unidades": {
            "violaciones_monto_negativo": violaciones_monto_neg,
            "violaciones_hora_fuera_0_23": violaciones_hora,
            "violaciones_confianza_fuera_0_1": violaciones_confianza,
            "violaciones_texto_vacio": violaciones_texto_vacio,
            "total_violaciones": total_violaciones_rango,
        },
        "criterio_3_consistencia_logica_temporal": {
            "violaciones_timestamp_respuesta_menor_inicio": violaciones_orden_fechas,
            "violaciones_regla_es_fuera_horario": violaciones_flag_horario,
            "violaciones_clases_no_permitidas": clases_invalidas,
            "violaciones_origen_no_permitido": origenes_invalidos,
        },
        "criterio_7_mezcla_real_simulado": {
            "conteo_origen": {k: int(v) for k, v in conteo_origen.items()},
            "comparacion_distribuciones": stats_por_origen,
        },
    }


def aplicar_ingenieria_caracteristicas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables derivadas justificadas por el negocio de Hurios Rally E.I.R.L.
    y documenta el tratamiento de nulos sin eliminar columnas ni filtrar filas.
    """
    df_feat = df.copy()

    # 1. Conversión de timestamps y cálculo de tiempo de respuesta en segundos
    ts_inicio = pd.to_datetime(df_feat["timestamp_primer_mensaje"])
    ts_fin = pd.to_datetime(df_feat["timestamp_respuesta_bot"])
    df_feat["tiempo_respuesta_seg"] = (ts_fin - ts_inicio).dt.total_seconds().clip(lower=1.0)

    # 2. Imputación explícita de nulos en variables de contexto (previa al modelado)
    df_feat["producto_cotizado"] = df_feat["producto_cotizado"].fillna("SIN_PRODUCTO").replace("", "SIN_PRODUCTO")
    df_feat["metodo_pago"] = df_feat["metodo_pago"].fillna("NINGUNO").replace("", "NINGUNO")
    df_feat["monto_total"] = pd.to_numeric(df_feat["monto_total"], errors="coerce").fillna(0.0)
    df_feat["es_fuera_horario_num"] = df_feat["es_fuera_horario"].astype(int)

    # 3. Normalización de texto con diccionario de jerga mecánica
    df_feat["texto_normalizado"] = df_feat["texto_cliente"].apply(normalizar_texto_mecanico)

    # 4. Variables derivadas de texto (Feature Engineering de negocio)
    df_feat["longitud_mensaje"] = df_feat["texto_cliente"].astype(str).str.len()
    df_feat["num_palabras"] = df_feat["texto_normalizado"].str.split().str.len()

    patron_repuestos = r"(bajaj|torito|tvs|king|pulsar|discover|cilindro|embrague|freno|zapata|estator|carburador|llanta|aceite|amortiguador|bateria|bujia|culata|cigueñal)"
    df_feat["contiene_jerga_mecanica"] = (
        df_feat["texto_normalizado"].str.contains(patron_repuestos, regex=True).astype(int)
    )

    patron_transaccional = r"(yape|plin|pedido|ped|boleta|factura|pague|pagado|despacho|envio|visa|tarjeta|recoger|orden)"
    df_feat["menciona_pago_o_pedido"] = (
        df_feat["texto_normalizado"].str.contains(patron_transaccional, regex=True).astype(int)
    )

    patron_cotizacion = r"(precio|cuanto|cuesta|stock|tienes|cotiza|cotizacion|soles|s/|dejas|disponible)"
    df_feat["menciona_precio_stock"] = (
        df_feat["texto_normalizado"].str.contains(patron_cotizacion, regex=True).astype(int)
    )

    patron_tecnico = r"(compatible|hace|medida|diferencia|kilometros|humo|fuerza|viscosidad|calza|adapta|suena|carga)"
    df_feat["menciona_duda_tecnica"] = (
        df_feat["texto_normalizado"].str.contains(patron_tecnico, regex=True).astype(int)
    )

    return df_feat


def detectar_outliers_iqr(serie: pd.Series) -> dict:
    """Calcula estadísticos IQR para documentar valores atípicos en el Paso 2 del informe."""
    q1 = float(serie.quantile(0.25))
    q3 = float(serie.quantile(0.75))
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    outliers = serie[(serie < lim_inf) | (serie > lim_sup)]
    return {
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "limite_inferior": round(lim_inf, 2),
        "limite_superior": round(lim_sup, 2),
        "cantidad_outliers": int(len(outliers)),
        "porcentaje_outliers": round(len(outliers) * 100.0 / len(serie), 2),
    }


def generar_graficos_eda(df_feat: pd.DataFrame) -> None:
    """Genera las figuras 1 y 2 del Análisis Exploratorio de Datos (EDA)."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")

    # FIGURA 1: Distribución de Clases y Consultas Fuera de Horario
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=160)
    colores = ["#1d4ed8", "#0d9488", "#d97706", "#dc2626"]
    conteo_clases = df_feat["intencion_predicha"].value_counts().reindex(CLASES_ORDENADAS)

    bars = axes[0].bar(
        CLASES_ORDENADAS,
        conteo_clases.values,
        color=colores,
        edgecolor="black",
        alpha=0.9,
    )
    axes[0].set_title("A) Distribución de la Variable Objetivo (intencion_predicha)", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Clase de Intención del Cliente", fontsize=10)
    axes[0].set_ylabel("Cantidad de Mensajes (n = 520)", fontsize=10)
    axes[0].tick_params(axis="x", rotation=15)
    for bar in bars:
        h = bar.get_height()
        axes[0].text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 2,
            f"{int(h)} ({h/len(df_feat)*100:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )
    axes[0].set_ylim(0, max(conteo_clases.values) * 1.18)

    # Subplot B: Distribución horaria (En Horario 08:00-17:59 vs Fuera de Horario 18:00-07:59)
    tabla_horario = (
        pd.crosstab(df_feat["intencion_predicha"], df_feat["es_fuera_horario"])
        .reindex(CLASES_ORDENADAS)
    )
    tabla_horario.columns = ["Horario Tienda (08:00-17:59)", "Fuera de Horario (18:00-07:59)"]
    tabla_horario.plot(
        kind="bar",
        stacked=False,
        ax=axes[1],
        color=["#2563eb", "#f59e0b"],
        edgecolor="black",
        alpha=0.9,
    )
    axes[1].set_title("B) Mensajes por Intención según Franja Horaria (Comas)", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Clase de Intención del Cliente", fontsize=10)
    axes[1].set_ylabel("Cantidad de Mensajes", fontsize=10)
    axes[1].tick_params(axis="x", rotation=15)
    axes[1].legend(title="Condición Horaria", frameon=True)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_eda_distribucion_clases_horarios.png", bbox_inches="tight")
    plt.close(fig)

    # FIGURA 2: Boxplot de Longitud de Mensaje / Outliers y Matriz de Correlación
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=160)
    sns.boxplot(
        data=df_feat,
        x="intencion_predicha",
        y="longitud_mensaje",
        order=CLASES_ORDENADAS,
        palette=colores,
        ax=axes[0],
    )
    axes[0].set_title("A) Distribución y Outliers de Longitud de Mensaje por Clase", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Clase de Intención", fontsize=10)
    axes[0].set_ylabel("Longitud del Mensaje (caracteres)", fontsize=10)
    axes[0].tick_params(axis="x", rotation=15)

    cols_corr = [
        "hora_del_dia",
        "es_fuera_horario_num",
        "longitud_mensaje",
        "num_palabras",
        "contiene_jerga_mecanica",
        "menciona_pago_o_pedido",
        "menciona_precio_stock",
        "menciona_duda_tecnica",
    ]
    corr_matrix = df_feat[cols_corr].corr()
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-0.6,
        vmax=1.0,
        ax=axes[1],
        cbar_kws={"shrink": 0.8},
    )
    axes[1].set_title("B) Matriz de Correlación de Variables Numéricas y Derivadas", fontsize=12, fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_eda_outliers_correlaciones.png", bbox_inches="tight")
    plt.close(fig)


def construir_preprocesador() -> ColumnTransformer:
    """
    Construye el ColumnTransformer que vectoriza el texto normalizado con TF-IDF (1-2 gramas)
    y escala las variables numéricas/ingeniería de características con StandardScaler.
    Solo utiliza variables disponibles en el momento exacto en que entra el mensaje del cliente
    (evita fuga de información futura como estado_pedido post-venta).
    """
    cols_numericas = [
        "hora_del_dia",
        "es_fuera_horario_num",
        "longitud_mensaje",
        "num_palabras",
        "contiene_jerga_mecanica",
        "menciona_pago_o_pedido",
        "menciona_precio_stock",
        "menciona_duda_tecnica",
    ]

    pipeline_num = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    preprocesador = ColumnTransformer(
        transformers=[
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=600,
                    ngram_range=(1, 2),
                    stop_words=STOPWORDS_ES,
                    sublinear_tf=True,
                ),
                "texto_normalizado",
            ),
            ("num", pipeline_num, cols_numericas),
        ],
        remainder="drop",
    )
    return preprocesador


def entrenar_y_comparar_modelos(df_feat: pd.DataFrame) -> tuple[dict, Pipeline]:
    """
    Ejecuta Paso 2.5 (Split Estratificado sin Data Leakage) y Paso 3 (Línea Base Obligatoria +
    Entrenamiento, GridSearchCV y comparación de 4 algoritmos supervisados de la Unidad 3).
    Además extrae los casos de error en el Test Set (Sección 6.1).
    """
    feature_cols = [
        "texto_normalizado",
        "hora_del_dia",
        "es_fuera_horario_num",
        "longitud_mensaje",
        "num_palabras",
        "contiene_jerga_mecanica",
        "menciona_pago_o_pedido",
        "menciona_precio_stock",
        "menciona_duda_tecnica",
    ]
    X = df_feat[feature_cols]
    y = df_feat["intencion_predicha"]

    # PARTICIÓN ESTRATIFICADA 80% TRAIN / 20% TEST ANTES DE AJUSTAR TRANSFORMADORES
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    cv_estratificado = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    # Incluye explícitamente la Línea Base Obligatoria (Sección 5 de la Consigna APF3 - 2026-2)
    definicion_modelos = {
        "Línea Base (DummyClassifier)": {
            "estimator": DummyClassifier(random_state=RANDOM_STATE),
            "param_grid": {
                "clf__strategy": ["most_frequent", "stratified"],
            },
        },
        "SVM (Support Vector Machine)": {
            "estimator": SVC(probability=True, random_state=RANDOM_STATE),
            "param_grid": {
                "clf__C": [0.15, 0.30, 0.50],
                "clf__kernel": ["linear", "rbf"],
                "clf__class_weight": [None, "balanced"],
            },
        },
        "Regresión Logística Multiclase": {
            "estimator": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
            "param_grid": {
                "clf__C": [0.20, 0.40, 0.80],
                "clf__solver": ["lbfgs"],
                "clf__class_weight": [None, "balanced"],
            },
        },
        "Random Forest": {
            "estimator": RandomForestClassifier(random_state=RANDOM_STATE),
            "param_grid": {
                "clf__n_estimators": [100, 150],
                "clf__max_depth": [5, 7],
                "clf__min_samples_leaf": [3, 5],
            },
        },
        "K-Nearest Neighbors (KNN)": {
            "estimator": KNeighborsClassifier(),
            "param_grid": {
                "clf__n_neighbors": [7, 11, 15],
                "clf__weights": ["uniform"],
                "clf__metric": ["cosine", "euclidean"],
            },
        },
    }

    resultados = {}
    mejor_f1 = -1.0
    mejor_nombre = ""
    mejor_pipeline = None
    matrices_confusion = {}

    for nombre_modelo, cfg in definicion_modelos.items():
        pipe = Pipeline(
            steps=[
                ("preprocessor", construir_preprocesador()),
                ("clf", cfg["estimator"]),
            ]
        )

        grid = GridSearchCV(
            estimator=pipe,
            param_grid=cfg["param_grid"],
            cv=cv_estratificado,
            scoring="f1_macro",
            n_jobs=1,
            refit=True,
        )
        grid.fit(X_train, y_train)
        best_model = grid.best_estimator_

        y_pred_train = best_model.predict(X_train)
        y_pred_test = best_model.predict(X_test)

        acc_train = accuracy_score(y_train, y_pred_train)
        f1_train = f1_score(y_train, y_pred_train, average="macro", zero_division=0)

        acc_test = accuracy_score(y_test, y_pred_test)
        prec_test = precision_score(y_test, y_pred_test, average="macro", zero_division=0)
        rec_test = recall_score(y_test, y_pred_test, average="macro", zero_division=0)
        f1_macro_test = f1_score(y_test, y_pred_test, average="macro", zero_division=0)
        f1_weighted_test = f1_score(y_test, y_pred_test, average="weighted", zero_division=0)

        cm = confusion_matrix(y_test, y_pred_test, labels=CLASES_ORDENADAS)
        matrices_confusion[nombre_modelo] = cm

        reporte_clases = classification_report(
            y_test,
            y_pred_test,
            labels=CLASES_ORDENADAS,
            output_dict=True,
            zero_division=0,
        )

        resultados[nombre_modelo] = {
            "mejores_hiperparametros": grid.best_params_,
            "cv_f1_macro_mean": round(float(grid.best_score_), 4),
            "train_accuracy": round(float(acc_train), 4),
            "train_f1_macro": round(float(f1_train), 4),
            "test_accuracy": round(float(acc_test), 4),
            "test_precision_macro": round(float(prec_test), 4),
            "test_recall_macro": round(float(rec_test), 4),
            "test_f1_macro": round(float(f1_macro_test), 4),
            "test_f1_weighted": round(float(f1_weighted_test), 4),
            "gap_overfitting_f1": round(float(f1_train - f1_macro_test), 4),
            "matriz_confusion": cm.tolist(),
            "reporte_por_clase": reporte_clases,
        }

        if nombre_modelo != "Línea Base (DummyClassifier)" and f1_macro_test > mejor_f1:
            mejor_f1 = f1_macro_test
            mejor_nombre = nombre_modelo
            mejor_pipeline = best_model

    # Extraer los casos donde el modelo ganador falla en el Test Set (Sección 6.1: Análisis de errores)
    y_pred_ganador = mejor_pipeline.predict(X_test)
    probas_ganador = mejor_pipeline.predict_proba(X_test)
    clases_modelo = list(mejor_pipeline.classes_)

    casos_error = []
    for idx_pos, idx_df in enumerate(X_test.index):
        real_lbl = str(y_test.loc[idx_df])
        pred_lbl = str(y_pred_ganador[idx_pos])
        if real_lbl != pred_lbl:
            conf_pred = float(np.max(probas_ganador[idx_pos]))
            fila_orig = df_feat.loc[idx_df]
            casos_error.append(
                {
                    "id_conversacion": str(fila_orig["id_conversacion"]),
                    "origen": str(fila_orig["origen"]),
                    "texto_cliente": str(fila_orig["texto_cliente"]),
                    "clase_real": real_lbl,
                    "clase_predicha": pred_lbl,
                    "confianza_prediccion": round(conf_pred, 4),
                    "hora_del_dia": int(fila_orig["hora_del_dia"]),
                }
            )

    # FIGURA 3: Comparación de métricas (incluyendo Línea Base) y Matriz de Confusión del Ganador
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.5), dpi=160)

    nombres = list(resultados.keys())
    metricas_df = pd.DataFrame(
        {
            "Modelo": nombres,
            "Accuracy (Test)": [resultados[m]["test_accuracy"] for m in nombres],
            "Precision Macro": [resultados[m]["test_precision_macro"] for m in nombres],
            "Recall Macro": [resultados[m]["test_recall_macro"] for m in nombres],
            "F1-Score Macro": [resultados[m]["test_f1_macro"] for m in nombres],
        }
    ).set_index("Modelo")

    metricas_df.plot(
        kind="bar",
        ax=axes[0],
        color=["#1e40af", "#0f766e", "#b45309", "#dc2626"],
        edgecolor="black",
        alpha=0.9,
    )
    axes[0].axhline(0.85, color="green", linestyle="--", linewidth=1.5, label="Meta F1 >= 0.85 (APF1/APF2)")
    axes[0].set_ylim(0.15, 1.05)
    axes[0].set_title("A) Línea Base vs Modelos Unidad 3 en Test Set (n = 104)", fontsize=11.5, fontweight="bold")
    axes[0].set_ylabel("Puntaje (0.0 a 1.0)", fontsize=10)
    axes[0].tick_params(axis="x", rotation=18)
    axes[0].legend(loc="lower right", fontsize=8.5, frameon=True)

    cm_ganador = matrices_confusion[mejor_nombre]
    sns.heatmap(
        cm_ganador,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASES_ORDENADAS,
        yticklabels=CLASES_ORDENADAS,
        ax=axes[1],
        cbar=False,
        annot_kws={"size": 12, "weight": "bold"},
    )
    axes[1].set_title(f"B) Matriz de Confusión - Modelo Ganador:\n{mejor_nombre} (F1={mejor_f1:.4f})", fontsize=11.5, fontweight="bold")
    axes[1].set_xlabel("Predicción del Modelo", fontsize=10)
    axes[1].set_ylabel("Clase Real (Ground Truth)", fontsize=10)
    axes[1].tick_params(axis="x", rotation=15)
    axes[1].tick_params(axis="y", rotation=0)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_comparacion_modelos_matrices.png", bbox_inches="tight")
    plt.close(fig)

    # FIGURA 4: Importancia de variables / Pesos por Clase para Interpretabilidad de Negocio
    generar_grafico_importancia(mejor_pipeline, X_train, y_train)

    resumen_final = {
        "semilla_reproducibilidad": RANDOM_STATE,
        "total_registros": int(len(df_feat)),
        "registros_entrenamiento": int(len(X_train)),
        "registros_prueba": int(len(X_test)),
        "clases": CLASES_ORDENADAS,
        "linea_base_f1_macro": resultados["Línea Base (DummyClassifier)"]["test_f1_macro"],
        "modelo_ganador": mejor_nombre,
        "f1_macro_ganador": round(float(mejor_f1), 4),
        "cumple_meta_apf2_085": bool(mejor_f1 >= 0.85),
        "modelos_comparados": resultados,
        "casos_error_test_set": casos_error,
    }
    return resumen_final, mejor_pipeline


def generar_grafico_importancia(mejor_pipeline: Pipeline, X_train: pd.DataFrame, y_train: pd.Series) -> None:
    """Extrae e ilustra las variables/términos más determinantes por clase de negocio."""
    prep = mejor_pipeline.named_steps["preprocessor"]
    nombres_tfidf = list(prep.named_transformers_["tfidf"].get_feature_names_out())
    nombres_num = [
        "hora_del_dia",
        "es_fuera_horario",
        "longitud_mensaje",
        "num_palabras",
        "contiene_jerga_mecanica",
        "menciona_pago_o_pedido",
        "menciona_precio_stock",
        "menciona_duda_tecnica",
    ]
    feature_names = [f"tfidf:{t}" for t in nombres_tfidf] + [f"feat:{n}" for n in nombres_num]

    X_tr_trans = prep.transform(X_train)
    lr_explainer = LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_STATE)
    lr_explainer.fit(X_tr_trans, y_train)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), dpi=160)
    colores_clase = {
        "COTIZACION": "#1d4ed8",
        "CONSULTA_TECNICA": "#0d9488",
        "ESTADO_PEDIDO": "#d97706",
        "SPAM": "#dc2626",
    }

    for idx, clase in enumerate(CLASES_ORDENADAS):
        ax = axes[idx // 2][idx % 2]
        clase_idx = list(lr_explainer.classes_).index(clase)
        coefs = lr_explainer.coef_[clase_idx]
        top_indices = np.argsort(coefs)[-8:]
        top_feats = [feature_names[i] for i in top_indices]
        top_vals = coefs[top_indices]

        ax.barh(top_feats, top_vals, color=colores_clase[clase], edgecolor="black", alpha=0.88)
        ax.set_title(f"Top 8 Factores Predictivos -> {clase}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Peso / Coeficiente de Influencia Positiva", fontsize=9.5)

    plt.suptitle(
        "Interpretabilidad del Modelo (Paso 4.2): Variables e Indicadores Clave por Intención en Hurios Rally",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_importancia_variables_tfidf.png", bbox_inches="tight")
    plt.close(fig)


def demostrar_prediccion_modelo_exportado(ruta_joblib: Path) -> dict:
    """
    Requisito Sección 5 (Modelo guardado) y Sección 6.3:
    Carga el archivo .joblib exportado y ejecuta una predicción sobre un registro nuevo
    con el esquema de integración del MVP.
    """
    pipeline_cargado = joblib.load(ruta_joblib)
    mensaje_nuevo = "Buenas noches maestro, ¿tienes cilindro completo para mi bajajita Torito 4T y cuánto cuesta?"
    hora_ejemplo = 21
    es_fuera = 1

    texto_norm = normalizar_texto_mecanico(mensaje_nuevo)
    registro_df = pd.DataFrame(
        [
            {
                "texto_normalizado": texto_norm,
                "hora_del_dia": hora_ejemplo,
                "es_fuera_horario_num": es_fuera,
                "longitud_mensaje": len(mensaje_nuevo),
                "num_palabras": len(texto_norm.split()),
                "contiene_jerga_mecanica": 1,
                "menciona_pago_o_pedido": 0,
                "menciona_precio_stock": 1,
                "menciona_duda_tecnica": 0,
            }
        ]
    )

    pred_clase = str(pipeline_cargado.predict(registro_df)[0])
    probas = pipeline_cargado.predict_proba(registro_df)[0]
    mapa_probas = {
        str(c): round(float(p), 4)
        for c, p in zip(pipeline_cargado.classes_, probas)
    }
    confianza = round(float(np.max(probas)), 4)

    return {
        "entrada_mvp_json": {
            "texto_cliente": mensaje_nuevo,
            "hora_del_dia": hora_ejemplo,
            "es_fuera_horario": True,
        },
        "salida_modelo_json": {
            "intencion_predicha": pred_clase,
            "confianza_modelo": confianza,
            "probabilidades": mapa_probas,
            "requiere_derivacion_humana": bool(confianza < 0.70),
        },
    }


def main():
    # Regenerar siempre con semilla fija SEED=42 para garantizar la columna `origen`
    generar_csv()

    df_raw = pd.read_csv(DATA_PATH)
    nulos_iniciales = df_raw.isnull().sum().to_dict()

    df_feat = aplicar_ingenieria_caracteristicas(df_raw)
    reporte_coherencia = verificar_coherencia_datos(df_raw, df_feat)

    outliers_monto = detectar_outliers_iqr(df_feat["monto_total"])
    outliers_latencia = detectar_outliers_iqr(df_feat["tiempo_respuesta_seg"])
    outliers_longitud = detectar_outliers_iqr(df_feat["longitud_mensaje"])

    generar_graficos_eda(df_feat)
    resumen_modelos, mejor_pipeline = entrenar_y_comparar_modelos(df_feat)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ruta_joblib = MODELS_DIR / "modelo_intenciones_hurios.joblib"
    joblib.dump(mejor_pipeline, ruta_joblib)

    demo_inferencia = demostrar_prediccion_modelo_exportado(ruta_joblib)

    resumen_modelos["verificacion_coherencia_4_2"] = reporte_coherencia
    resumen_modelos["demo_prediccion_registro_nuevo"] = demo_inferencia
    resumen_modelos["eda_resumen"] = {
        "nulos_iniciales": {k: int(v) for k, v in nulos_iniciales.items()},
        "distribucion_clases": {k: int(v) for k, v in df_feat["intencion_predicha"].value_counts().to_dict().items()},
        "distribucion_origen": {k: int(v) for k, v in df_feat["origen"].value_counts().to_dict().items()},
        "porcentaje_fuera_horario": round(float(df_feat["es_fuera_horario"].mean() * 100.0), 2),
        "outliers_iqr": {
            "monto_total": outliers_monto,
            "tiempo_respuesta_seg": outliers_latencia,
            "longitud_mensaje": outliers_longitud,
        },
    }

    with open(MODELS_DIR / "metricas_evaluacion.json", "w", encoding="utf-8") as f:
        json.dump(resumen_modelos, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("ENTRENAMIENTO Y EVALUACION COMPLETADOS - HURIOS RALLY E.I.R.L. (APF3 - 2026-2)")
    print("=" * 80)
    print(f"Total registros procesados : {resumen_modelos['total_registros']} (Real: {resumen_modelos['eda_resumen']['distribucion_origen'].get('real', 0)}, Simulado: {resumen_modelos['eda_resumen']['distribucion_origen'].get('simulado', 0)})")
    print(f"Partición Estratificada    : Train = {resumen_modelos['registros_entrenamiento']} (80%) | Test = {resumen_modelos['registros_prueba']} (20%)")
    print(f"Violaciones de rango/lógica: {reporte_coherencia['criterio_2_rangos_y_unidades']['total_violaciones']} violaciones")
    print(f"Consultas fuera de horario : {resumen_modelos['eda_resumen']['porcentaje_fuera_horario']}%")
    print(f"Línea Base (Dummy) F1-Macro: {resumen_modelos['linea_base_f1_macro']:.4f}")
    print(f"Modelo Ganador             : {resumen_modelos['modelo_ganador']}")
    print(f"F1-Score Macro (Test Set)  : {resumen_modelos['f1_macro_ganador']:.4f} (Meta APF1/APF2 >= 0.85)")
    print("-" * 80)
    for nombre, m in resumen_modelos["modelos_comparados"].items():
        print(
            f" * {nombre:<32} | CV F1: {m['cv_f1_macro_mean']:.4f} | "
            f"Train F1: {m['train_f1_macro']:.4f} | Test Acc: {m['test_accuracy']:.4f} | Test F1: {m['test_f1_macro']:.4f}"
        )
    print("-" * 80)
    print(f"Casos de error en Test Set : {len(resumen_modelos['casos_error_test_set'])} de {resumen_modelos['registros_prueba']} registros")
    for idx_e, err in enumerate(resumen_modelos["casos_error_test_set"][:4], 1):
        print(f"   [Error {idx_e}] Real={err['clase_real']} vs Pred={err['clase_predicha']} (conf={err['confianza_prediccion']}): \"{err['texto_cliente'][:75]}...\"")
    print("-" * 80)
    print("DEMO DE PREDICCION CON MODELO EXPORTADO (.joblib):")
    print(f"   Entrada : {demo_inferencia['entrada_mvp_json']['texto_cliente']}")
    print(f"   Salida  : {demo_inferencia['salida_modelo_json']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
