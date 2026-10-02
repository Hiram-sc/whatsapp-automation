from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router

app = FastAPI()

app.mount("/static", StaticFiles(directory="front/static"), name="static")

app.include_router(router)