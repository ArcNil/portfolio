from fastapi import Depends, FastAPI, Header, HTTPException

from app.config import Settings, get_settings
from app.forex_forecast.routes import router as forex_forecast_router


def require_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Reject the request with 401 if the X-API-Key header doesn't match WORKER_API_KEY."""
    if settings.worker_api_key and x_api_key != settings.worker_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


app = FastAPI(title="Portfolio Workers")
app.include_router(
    forex_forecast_router,
    prefix="/forex-forecast",
    tags=["forex-forecast"],
    dependencies=[Depends(require_api_key)],
)


@app.get("/")
async def hello_world() -> dict[str, str]:
    """Health-check endpoint returning a simple greeting."""
    return {"message": "Hello, World!"}
