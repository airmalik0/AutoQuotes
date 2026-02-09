import logging
import pathlib

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import cars, requests

logger = logging.getLogger(__name__)

STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
UPLOADS_DIR = pathlib.Path(__file__).resolve().parent.parent / "uploads"


def create_app() -> FastAPI:
    app = FastAPI(title="AutoQuotes API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error("Validation error: %s", exc.errors())
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    app.include_router(cars.router)
    app.include_router(requests.router)

    # Mount static files (built React app)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    # Mount uploads
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

    return app
