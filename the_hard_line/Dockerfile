FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libpq-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apk del gcc musl-dev

COPY app ./app
COPY static ./static
COPY templates ./templates
COPY main.py .

EXPOSE 6969

ENV PYTHONUNBUFFERED=1
ENV DB_HOST=postgres-egypt
ENV DB_PORT=5432
ENV DB_USER=loay
ENV DB_PASS=2004
ENV DB_NAME=egypt_users

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6969", "--workers", "1"]
