import logging

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from fastapi_pagination import add_pagination

from configs.config import settings 

def init_app():

    description = """
        This is a service for Land Aqusition
    """

    app = FastAPI(title="Landrope",
                  description=description,
                  version="1.0",
                  docs_url="/landrope/docs",
                  redoc_url="/landrope/redoc")
    
    @app.on_event("startup")
    async def startup():
        pass

    @app.get("/")
    async def home():
        return{"Message" : "Welcome Home"}
    
    app.add_middleware(SQLAlchemyMiddleware,
                       db_url=settings.DB_CONFIG,
                       engine_args={"echo" : False, "pool_pre_ping" : True, "pool_recycle" : 1800})
    
    add_pagination(app)
    
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