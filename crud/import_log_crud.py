from fastapi import UploadFile, HTTPException
from fastapi_async_sqlalchemy import db

from crud.base_crud import CRUDBase
from models.import_log_model import ImportLog
from schemas.import_log_sch import ImportLogCreateSch, ImportLogUpdateSch
from services.gcloud_storage_service import GCStorage
from uuid import UUID
from datetime import datetime

from sqlalchemy import exc
from sqlmodel.ext.asyncio.session import AsyncSession


class CRUDImportLog(CRUDBase[ImportLog, ImportLogCreateSch, ImportLogUpdateSch]):
    async def upload_file(
            self, file,
            obj_current: ImportLog,
            worker_id: UUID,
            db_session: AsyncSession | None = None):
        file_path, file_name = await GCStorage().upload_zip(file=file)

        db_session = db_session or db.session
        obj_current.file_path = file_path
        obj_current.file_name = file_name
        obj_current.updated_by_id = worker_id
        db_session.add(obj_current)

        await db_session.commit()
        return obj_current

    async def create(
        self,
        *,
        obj_in: ImportLogCreateSch,
        worker_id: UUID | str | None = None,
        db_session: AsyncSession | None = None,
        file: UploadFile | None = None
    ) -> ImportLog:
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in)  # type: ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()

        db_obj.created_by_id = worker_id
        db_obj.updated_by_id = worker_id

        try:
            db_session.add(db_obj)
            await db_session.commit()
            if file:
                await self.upload_file(file=file,
                                        obj_current=db_obj,
                                        worker_id=worker_id,
                                        db_session=db_session)

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Resource already exists",
            )
        await db_session.refresh(db_obj)
        return db_obj

import_log = CRUDImportLog(ImportLog)