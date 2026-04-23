FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r pip-requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 5001

CMD ["sh", "-c", "echo \"[backend] Starting Flask API on port ${MAIN_PORT:-5001}\" && exec python -m main.app"]
