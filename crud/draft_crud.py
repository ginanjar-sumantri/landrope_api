from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from crud.base_crud import CRUDBase
from models.draft_model import Draft, DraftDetail
from schemas.draft_sch import DraftCreateSch, DraftUpdateSch, DraftForAnalisaSch
from uuid import UUID
from datetime import datetime

class CRUDDraft(CRUDBase[Draft, DraftCreateSch, DraftUpdateSch]):
    async def create_for_analisa(self, *, 
                     obj_in: DraftForAnalisaSch, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> Draft :
        
        db_session = db_session or db.session
        db_obj = Draft.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
        
        try:

            for i in obj_in.details:
                detail = DraftDetail(bidang_id=i.bidang_id, geom=i.geom)

                db_obj.details.append(detail)

            db_session.add(db_obj)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)
        return db_obj

draft = CRUDDraft(Draft)