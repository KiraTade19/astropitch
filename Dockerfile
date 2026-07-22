# AstroPitch Prediction API - portable image (Render / Railway / Fly / any host)
FROM python:3.13-slim

# xgboost needs the OpenMP runtime
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# only what the API needs at runtime (incl. clubelo European fallback deps)
COPY app.py 24_api.py esoteric_features.py cosmic_reading.py \
     27_euro_predict.py 21_club_genesis.py \
     club_engine.pkl pro_engine.pkl ./

EXPOSE 8000
# hosts inject $PORT; default to 8000 locally
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
