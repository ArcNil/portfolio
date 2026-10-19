FROM python:3.10-alpine
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /uvx /bin/

COPY . .

RUN uv sync --locked

EXPOSE 8000

# WORKDIR /src/app

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn src.portfolio_workers.app:app --host 0.0.0.0 --port 8000"]

# CMD ["uv", "run", "uvicorn", "src.portfolio_workers.app:app", "--host", "0.0.0.0", "--port", "8000"]