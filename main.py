import logging
import os

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from fastapi_pagination import add_pagination
from fastapi_async_sqlalchemy import db
from starlette.middleware.cors import CORSMiddleware

from services.closing_service import ClosingService

from configs.config import settings 
from routes import api
import pytz
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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

    @app.get("/")
    async def home():
        return{"Message" : "Welcome Home"}
    
    app.add_middleware(SQLAlchemyMiddleware,
                       db_url=settings.DB_CONFIG,
                       engine_args={"echo" : False, "pool_pre_ping" : True, "pool_recycle" : 1800})
    
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
scheduler = BackgroundScheduler()

# FUNGSI UTAMA UNTUK CRON JOB
# - CLOSING TIAP TANGGAL 1
async def cron_job_bulanan():
    async with db():
        await ClosingService().closing_bidang()
        await ClosingService().closing_kulit_planing()
        await ClosingService().closing_kjb_dt()

# UNTUK MENJALANKAN FUNGSI ASYNC PADA CRON JOB
def run_async_cron_job(job_func):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(job_func())
    loop.close()

# SET JADWAL BULANAN CRON JOB
def jadwal_bulanan_cron_job():
    trigger = CronTrigger(day='2', hour='0', minute='1')
    scheduler.add_job(run_async_cron_job, trigger, args=[cron_job_bulanan])
    scheduler.start()

# JALANKAN CRON JOB SAAT APLIKASI STARTUP
@app.on_event("startup")
async def startup_event():
    jadwal_bulanan_cron_job()

# MATIKAN CRON JOB SAAT APLIKASI SHUTDOWN
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()