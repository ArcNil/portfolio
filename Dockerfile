FROM python:3.12-slim

WORKDIR /app

# Installed console scripts (alembic, uvicorn) don't add the working
# directory to sys.path, so make the app package importable explicitly.
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY scripts ./scripts

EXPOSE 7860

CMD ["sh", "scripts/start.sh"]
