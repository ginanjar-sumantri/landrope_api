from fastapi import UploadFile, HTTPException
from fastapi_async_sqlalchemy import db

from crud.base_crud import CRUDBase
from models.export_log_model import ExportLog
from schemas.export_log_sch import ExportLogCreateSch, ExportLogUpdateSch
from services.gcloud_storage_service import GCStorageService
from uuid import UUID
from datetime import datetime

from sqlalchemy import exc
from sqlmodel.ext.asyncio.session import AsyncSession


class CRUDExportLog(CRUDBase[ExportLog, ExportLogCreateSch, ExportLogUpdateSch]):
    pass

export_log = CRUDExportLog(ExportLog)