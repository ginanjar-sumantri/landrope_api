from fastapi import UploadFile, HTTPException
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.sql.expression import Select
from crud.base_crud import CRUDBase
from models.export_log_model import ExportLog
from schemas.export_log_sch import ExportLogCreateSch, ExportLogUpdateSch
from common.enum import TaskStatusEnum
from uuid import UUID
from datetime import datetime, date

from sqlalchemy import exc
from sqlmodel.ext.asyncio.session import AsyncSession


class CRUDExportLog(CRUDBase[ExportLog, ExportLogCreateSch, ExportLogUpdateSch]):

    async def get_export_expired(self, *, db_session : AsyncSession | None = None) -> list[ExportLog] | None:
        db_session = db_session or db.session

        today = date.today()
        query = select(ExportLog).where(and_(ExportLog.expired_date < today, ExportLog.status != TaskStatusEnum.Expired))
        response =  await db_session.execute(query)
        return response.scalars().all()
     

export_log = CRUDExportLog(ExportLog)