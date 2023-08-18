from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumenHd
from schemas.checklist_kelengkapan_dokumen_hd_sch import ChecklistKelengkapanDokumenHdCreateSch, ChecklistKelengkapanDokumenHdUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime

class CRUDChecklistKelengkapanDokumenHd(CRUDBase[ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenHdCreateSch, ChecklistKelengkapanDokumenHdUpdateSch]):
    async def create_and_generate(self, *, 
                     obj_in: ChecklistKelengkapanDokumenHd, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> ChecklistKelengkapanDokumenHd :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
        
        try:
            if len(obj_in.details) > 0:
                db_obj.details = obj_in.details

            db_session.add(db_obj)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)
        return db_obj

checklist_kelengkapan_dokumen_hd = CRUDChecklistKelengkapanDokumenHd(ChecklistKelengkapanDokumenHd)