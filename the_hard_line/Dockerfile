FROM python:3.11-alpine

WORKDIR /app

# Install build dependencies for asyncpg (gcc, musl-dev)
RUN apk add --no-cache gcc musl-dev libpq-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove build deps to keep image small
RUN apk del gcc musl-dev

COPY main.py .

EXPOSE 6969

ENV PYTHONUNBUFFERED=1
ENV DB_HOST=192.168.1.201
ENV DB_PORT=5432
ENV DB_USER=loay
ENV DB_PASS=2004
ENV DB_NAME=egypt_users

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6969", "--workers", "1"]
