# Stage 1: Build CSS with Node
FROM node:20-alpine AS build-css
WORKDIR /app
COPY alarino_frontend/package*.json ./
RUN npm install
COPY alarino_frontend /app/static
WORKDIR /app/static
RUN npm run build:css


# Stage 2: Python app
FROM python:3.11-slim

# Install dependencies needed after slim python
RUN apt-get update && apt-get install -y gcc libpq-dev curl

# Set working directory in container
WORKDIR /app

# Copy project files
COPY alarino_backend /app
COPY --from=build-css /app/static ./static

RUN pip install --no-cache-dir -r pip-requirements.txt

# Set flask_specific environment variables (override in .env or docker-compose)
# ENV FLASK_APP=main/app.py
# ENV FLASK_RUN_PORT=5001

# let logs output immediately without python buffering
# ENV PYTHONUNBUFFERED=1

# Expose flask port
EXPOSE 5001

# Run the app
# CMD ["flask", "run", "--host=0.0.0.0"]
CMD ["python", "-m", "main.app"]
