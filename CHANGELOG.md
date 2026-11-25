# CHANGELOG — HURIOS RALLY E.I.R.L. (`APF2 → APF3 → PROY Semana 17`)

Registro oficial de evolución técnica, correcciones metodológicas auditadas y validaciones del ecosistema **Hurios Rally E.I.R.L. (RUC 20492248933)**.

---

## `[v2.1.0]` — 2026-11-24 (Proyecto Final Integrado · PROY Semana 17 — Corrección Total de Hallazgos APF3)

### 1. Corrección Integral del Modelo Base (Paso 2a) y Condición 5 (30 Registros Reales de Bitácora)
- **Eliminación de etiquetado sintético como real (`OBS-APF3-01` / Hallazgo 3.1)**: Se eliminó por completo la regla `idx % 4 == 0` en `generate_dataset.py`. Las **490 filas** generadas por plantillas calibradas van rotuladas 100 % como `origen = 'simulado'` (ningún dato simulado se presenta como real). Únicamente los **30 registros orgánicos capturados de las pruebas reales en vivo del Bot WhatsApp (`+51 937 395 986`) y de la sesión con la MiPYME** llevan `origen = 'real'` y se reservan 100 % fuera del entrenamiento para la validación externa caso por caso (**Condición 5**, logrando **28/30 aciertos = 93.33 % de exactitud**, `F1-Macro = 0.9329` y `0` falsos positivos en `SPAM`).
- **Selección del modelo ganador estrictamente por Validación Cruzada 5-Fold en Train (`OBS-APF3-02` / Hallazgo 3.2)**: En `train_pipeline.py`, el ganador se elige por el mayor `cv_f1_macro_mean` sobre `X_train` (`n = 392`), manteniendo `X_test` (`n = 98`) intacto hasta la evaluación final única. Se calculan y exportan en código `cv_f1_macro_std` (`± desv.`) y `test_roc_auc_ovr` (`roc_auc_score` multiclase OVR).
- **Unificación de schema de 13 columnas y limpieza del CSV (`OBS-APF3-03` y `OBS-APF3-04` / Hallazgos 3.3, 3.4 y 3.5)**:
  - `0` celdas vacías y `0` nulos (`NaN`) en las `520 × 13 = 6,760` celdas del CSV (`SIN_PRODUCTO`, `0.0`, `NINGUNO`, `SIN_PEDIDO`).
  - `0` números telefónicos de 9 dígitos en los 520 textos (`conteo_telefonos_9_digitos_pii = 0`).
  - Rango de `monto_total` acotado estrictamente a `[0.00, 960.00]` (`S/ 18.00` a `S/ 960.00` en cotizaciones positivas, ticket medio `S/ 127.89`).
  - Script `train_pipeline.py` (`PROY_TD_Grupo01_codigo.py`) 100 % autocontenido (no falla si se ejecuta sin `generate_dataset.py`).

### 2. Ciclo de Mejora del Modelo Corregido (Paso 2b)
- **3 nuevas variables derivadas justificadas por el negocio**:
  1. `tiene_especificacion_modelo`: Detecta patrones de spam mayorista B2B, préstamos o sorteos que emplean palabras del rubro.
  2. `indicador_cierre_venta`: Cruza mención de repuesto mecánico con urgencia de compra/stock inmediato.
  3. `ratio_densidad_comercial`: Captura señales explícitas de comprobantes posventa o medidas técnicas en milímetros.
- **Reajuste de preprocesamiento e hiperparámetros (`GridSearchCV` 5-Fold solo en Train)**: Ampliación controlada a `850` unigramas y bigramas TF-IDF y optimización del umbral de decisión por costo en Soles (`0.68` general / `0.80` para `SPAM`).
- **Mejora demostrada bajo la misma partición (`392 Train / 98 Test`, `SEED = 42`)**:
  - `0. Línea Base (DummyClassifier)`: `CV F1 = 0.2579 ± 0.0791` | `Test F1-Macro = 0.1441` | `Test Accuracy = 15.31%`
  - `1. Modelo APF3 Entregado (Referencia Sem. 15)`: `CV F1 = 0.9422` | `Test F1-Macro = 0.9393` | `Test Accuracy = 94.23%`
  - `2. Modelo Base APF3 Corregido (Paso 2a)`: `CV F1 = 0.9108` | `Test F1-Macro = 0.8483` | `Test Accuracy = 84.69%`
  - `3. Modelo PROY Mejorado (Paso 2b — Regresión Logística Multiclase, ganador por CV)`: **`CV F1 = 0.9657 ± 0.0165` | `Test F1-Macro = 0.9523` (`+10.40 puntos` sobre el modelo base corregido, `Test Accuracy = 94.90%`, `ROC-AUC = 0.9956` y `Precisión SPAM = 100%`)**.

### 3. Extensión de Semana 16 — Clustering No Supervisado (`Sección 9 · +0.5 pts`)
- Implementación de **K-Means (`k = 4`, `random_state = 42`)** comparado contra `k = 3, 4, 5` y Clustering Jerárquico Aglomerativo (`Silhouette = 0.2820`, `Davies-Bouldin = 1.3738`), identificando 4 perfiles operativos accionables sobre el dataset completo (`n = 520`).

### 4. Demo Funcional End-to-End, Validaciones y Degradación Controlada (Paso 3)
- **Modelo servido versionado**: Exportación de `models/modelo_intenciones_hurios.joblib` (`68.3 KB`, versión `v2.1.0-PROY-20261124`, hash SHA-256 `dd4330893381`), umbral configurable y registro persistente en `/predictions-log`.
- **Validación de entradas inválidas (`HTTP 422`)**: Rechazo controlado de textos vacíos, mensajes de solo símbolos (`"???"`) u horas fuera de `[0..23]`.
- **Protocolo de Degradación Controlada (`DEGRADACION_CONTROLADA_FALLBACK`)**: Regla manual de respaldo y escalamiento automático al asesor humano (`+51 937 395 986`) cuando el motor ML no responde o recibe una consulta con confianza inferior al umbral seguro.

---

## `[v1.5.0]` — 2026-11-10 (Avance de Proyecto Final 3 · APF3 Semana 15)
- Entrenamiento inicial sobre 520 registros, microservicio FastAPI (`POST /predict`), puente de WhatsApp Multi-Device (`+51 937 395 986`) con menú interactivo de categorías y Bandeja Analítica con gráficas estilo Power BI.

---

## `[v1.0.0]` — 2026-10-12 (Avance de Proyecto Final 2 · APF2 Semana 10)
- Despliegue del MVP Full-Stack (Frontend React + Backend Spring Boot + Base de Datos Supabase PostgreSQL con 48 repuestos reales, carrito de compras, pagos Yape/Tarjeta y emisión de Boleta de Venta Electrónica).
