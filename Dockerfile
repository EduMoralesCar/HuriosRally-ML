FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Genera el dataset y entrena el modelo al construir la imagen para garantizar reproducibilidad (random_state=42)
RUN python generate_dataset.py && python train_pipeline.py

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
