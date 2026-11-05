import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.api.routes import encerrar_recursos, router


logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicação.")
    yield
    logger.info("Encerrando aplicação.")
    await encerrar_recursos()


app = FastAPI(lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(config.STATIC_DIR)),
    name="static",
)

app.include_router(router)
