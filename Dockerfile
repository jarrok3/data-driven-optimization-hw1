FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .env /app/.env

RUN chmod +x /app/scripts/init.sh

ENTRYPOINT ["/app/scripts/init.sh"]