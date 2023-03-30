from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from crud.base_crud import CRUDBase
from models.planing_model import Planing
from schemas.planing_sch import PlaningCreateSch, PlaningUpdateSch
from sqlalchemy import exc
from datetime import datetime

class CRUDPlaning(CRUDBase[Planing, PlaningCreateSch, PlaningUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> Planing:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Planing).where(Planing.name == name))
        return obj.scalar_one_or_none()
    
    async def get_by_project_id_desa_id(
        self, *, project_id: str, desa_id:str, db_session: AsyncSession | None = None
    ) -> Planing:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Planing).where(and_(Planing.project_id == project_id, Planing.desa_id == desa_id)))
        return obj.scalar_one_or_none()
    
    async def create_planing(self, *, obj_in: Planing, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> PlaningCreateSch :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
        
        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj

planing = CRUDPlaning(Planing)