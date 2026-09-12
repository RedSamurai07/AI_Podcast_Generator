FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8501
EXPOSE 8501

CMD mkdir -p .streamlit && cp /etc/secrets/secrets.toml .streamlit/secrets.toml && \
    streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true