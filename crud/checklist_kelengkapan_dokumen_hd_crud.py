from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt, Bidang
from schemas.checklist_kelengkapan_dokumen_hd_sch import ChecklistKelengkapanDokumenHdCreateSch, ChecklistKelengkapanDokumenHdUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime

class CRUDChecklistKelengkapanDokumenHd(CRUDBase[ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenHdCreateSch, ChecklistKelengkapanDokumenHdUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> ChecklistKelengkapanDokumenHd | None:
        
        db_session = db_session or db.session
        
        query = select(ChecklistKelengkapanDokumenHd).where(ChecklistKelengkapanDokumenHd.id == id
                                                            ).options(selectinload(ChecklistKelengkapanDokumenHd.details
                                                                                    ).options(selectinload(ChecklistKelengkapanDokumenDt.bundle_dt)
                                                                                    ).options(selectinload(ChecklistKelengkapanDokumenDt.dokumen))
                                                            ).options(selectinload(ChecklistKelengkapanDokumenHd.bidang
                                                                                    ).options(selectinload(Bidang.bundlehd))
                                                            )
                                                    
                                                   
                                                    

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
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
    
    async def get_by_bidang_id(
        self, *, bidang_id: UUID, db_session: AsyncSession | None = None
    ) -> ChecklistKelengkapanDokumenHd:
        db_session = db_session or db.session
        obj = await db_session.execute(select(self.model).where(self.model.bidang_id == bidang_id))
        return obj.scalars().first()

checklist_kelengkapan_dokumen_hd = CRUDChecklistKelengkapanDokumenHd(ChecklistKelengkapanDokumenHd)