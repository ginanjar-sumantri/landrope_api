import logging
import os

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware

from configs.config import settings 
from routes import api
import pytz

def init_app():

    pytz.timezone("Asia/Jakarta")

    description = """
        This is a service for Land Aqusition
    """

    app = FastAPI(title="Landrope",
                description=description,
                version="1.0",
                docs_url="/landrope/docs",
                redoc_url="/landrope/redoc",
                openapi_url="/landrope/openapi.json")
    
    @app.on_event("startup")
    async def startup():
        pass

    @app.get("/")
    async def home():
        return{"Message" : "Welcome Home"}
    
    app.add_middleware(SQLAlchemyMiddleware,
                       db_url=settings.DB_CONFIG,
                       engine_args={"echo" : True, "pool_pre_ping" : True, "pool_recycle" : 1800})
    
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])
    
    app.include_router(api.api_router, prefix="/landrope")
    add_pagination(app)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
    
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger = logging.getLogger("gunicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = gunicorn_error_logger.handlers

    fastapi_logger.handlers = gunicorn_error_logger.handlers

    if __name__ != "__main__":
        fastapi_logger.setLevel(gunicorn_logger.level)
    else:
        fastapi_logger.setLevel(logging.DEBUG)

    return app

app = init_app()