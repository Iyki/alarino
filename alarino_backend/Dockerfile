FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 5001

CMD ["sh", "-c", "echo \"[backend] Starting Gunicorn on port ${MAIN_PORT:-5001}\" && exec gunicorn --bind 0.0.0.0:${MAIN_PORT:-5001} --workers ${GUNICORN_WORKERS:-2} --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-120} alarino_backend.wsgi:app"]
