# CHANGELOG — HURIOS RALLY E.I.R.L. (`APF2 → APF3 → PROY Semana 17`)

Registro oficial de evolución técnica, correcciones metodológicas y validaciones del ecosistema **Hurios Rally E.I.R.L. (RUC 20492248933)**.

---

## `[v2.0.0]` — 2026-11-24 (Proyecto Final Integrado · PROY Semana 17)

### 1. Corrección del Modelo Base (Paso 2a) y Condición 5 (30 Registros Reales)
- **Clarificación del propósito comercial y conexión con ventas (`OBS-APF3-01`)**: Se explicitó la relación causal entre la clasificación supervisada de intención en tiempo real (`COTIZACION`, `ESTADO_PEDIDO`, `CONSULTA_TECNICA`, `SPAM`) y el cierre de ventas nocturnas en `1.31 segundos`, incorporando el cálculo automático del **valor de venta potencial en Soles (`monto_potencial_soles`)** y la explicación en lenguaje de negocio (`explicacion_negocio`).
- **Separación estricta de 30 registros reales para validación externa (`Condición 5`)**: De los `130` registros con `origen = 'real'`, se reservaron **30 registros reales estratificados fuera del entrenamiento** (alcanzando **29/30 aciertos = 96.67% de exactitud** y `0` falsos positivos en `SPAM`).
- **Bonificación por datos reales en entrenamiento (`Sección 9 · +1 pto`)**: Los **100 registros reales adicionales** junto con los `390` simulados (`n = 490`) conforman el dataset de modelado (`392 Train / 98 Test`, `random_state = 42`).
- **Re-verificación en código de los 7 criterios de coherencia (`Condición 6`)**: Ejecución automatizada en `train_pipeline.py` con `0` violaciones de rango, lógica o fechas.

### 2. Ciclo de Mejora del Modelo Corregido (Paso 2b)
- **3 nuevas variables derivadas justificadas por el negocio**:
  1. `tiene_especificacion_modelo`: Detecta patrones de spam mayorista B2B, préstamos o sorteos que emplean palabras del rubro.
  2. `indicador_cierre_venta`: Cruza mención de repuesto mecánico con urgencia de compra/stock inmediato.
  3. `ratio_densidad_comercial`: Captura señales explícitas de comprobantes posventa o medidas técnicas en milímetros.
- **Reajuste de preprocesamiento e hiperparámetros (`GridSearchCV` 5-Fold solo en Train)**: Ampliación controlada a `850` unigramas y bigramas TF-IDF y optimización del umbral de decisión por costo en Soles (`0.68` general / `0.80` para `SPAM`).
- **Mejora demostrada bajo la misma partición (`392 Train / 98 Test`, `SEED = 42`)**:
  - `0. Línea Base (DummyClassifier)`: `F1-Macro = 0.2489` | `Accuracy = 25.51%`
  - `1. Modelo APF3 Entregado (Referencia Sem. 15)`: `F1-Macro = 0.9393` | `Accuracy = 94.23%`
  - `2. Modelo Base APF3 Corregido (Paso 2a)`: `F1-Macro = 0.9111` | `Accuracy = 90.82%`
  - `3. Modelo PROY Mejorado (Paso 2b — SVM Lineal)`: **`F1-Macro = 0.9404` (`+2.93 puntos` sobre el modelo corregido y `Precisión SPAM = 100%`)**.

### 3. Extensión de Semana 16 — Clustering No Supervisado (`Sección 9 · +0.5 pts`)
- Implementación de **K-Means (`k = 4`, `random_state = 42`)** comparado contra `k = 3, 4, 5` y Clustering Jerárquico Aglomerativo (`Silhouette = 0.3003`, `Davies-Bouldin = 1.3078`), identificando 4 perfiles accionables y confirmando que el segmento nocturno urgente presenta el ticket promedio más alto (`S/ 191.50`).

### 4. Demo Funcional End-to-End, Validaciones y Degradación Controlada (Paso 3)
- **Modelo servido versionado**: Exportación de `models/modelo_intenciones_hurios.joblib` con versión `v2.0.0-PROY-20261124`, hash SHA-256 `135c43a3eb29`, umbral configurable y registro persistente en `/predictions-log`.
- **Validación de entradas inválidas (`HTTP 422`)**: Rechazo controlado de textos vacíos, mensajes de solo símbolos (`"???"`) u horas fuera de `[0..23]`.
- **Protocolo de Degradación Controlada (`DEGRADACION_CONTROLADA_FALLBACK`)**: Regla manual de respaldo y escalamiento automático al asesor humano (`+51 937 395 986`) cuando el motor ML no responde o recibe una consulta con confianza inferior al umbral seguro.

---

## `[v1.5.0]` — 2026-11-10 (Avance de Proyecto Final 3 · APF3 Semana 15)
- Entrenamiento inicial sobre 520 registros (`130` reales + `390` simulados), microservicio FastAPI (`POST /predict`), puente de WhatsApp Multi-Device (`+51 937 395 986`) con menú interactivo de categorías y Bandeja Analítica con gráficas estilo Power BI.

---

## `[v1.0.0]` — 2026-10-12 (Avance de Proyecto Final 2 · APF2 Semana 10)
- Despliegue del MVP Full-Stack (Frontend React + Backend Spring Boot + Base de Datos Supabase PostgreSQL con 48 repuestos reales, carrito de compras, pagos Yape/Tarjeta y emisión de Boleta de Venta Electrónica).
