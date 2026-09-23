from pathlib import Path
from typing import Optional

import os

from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="pinggy-db-url")

URL_FILE = Path("/tmp/pinggy_url.txt")
SECRET_KEY = os.environ.get("SECRET_KEY", "")


def _check_api_key(api_key: str):
    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="SECRET_KEY is not configured")
    if api_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


def _read_url() -> Optional[str]:
    if not URL_FILE.exists():
        return None
    value = URL_FILE.read_text().strip()
    return value or None


@app.get("/")
def root(x_api_key: str = Header(default="")):
    _check_api_key(x_api_key)
    return {"status": "ok", "hint": "GET /db-url for the current connection info"}


@app.get("/db-url")
def db_url(x_api_key: str = Header(default="")):
    _check_api_key(x_api_key)
    url = _read_url()
    if url is None:
        raise HTTPException(status_code=503, detail="tunnel not ready yet, try again shortly")

    # url looks like tcp://<host>:<port>
    host_port = url[len("tcp://"):] if url.startswith("tcp://") else url
    host, _, port = host_port.partition(":")

    return {
        "tunnel_url": url,
        "host": host,
        "port": int(port) if port.isdigit() else None,
        "psql_example": f"psql -h {host} -p {port} -U postgres -d postgres",
    }
