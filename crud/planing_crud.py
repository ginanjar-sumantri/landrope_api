from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from crud.base_crud import CRUDBase
from models import Planing, Project
from schemas.planing_sch import PlaningCreateSch, PlaningUpdateSch
from sqlalchemy import exc
from datetime import datetime

class CRUDPlaning(CRUDBase[Planing, PlaningCreateSch, PlaningUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Planing | None:
        
        db_session = db_session or db.session
        
        query = select(Planing).where(Planing.id == id
                                        ).options(selectinload(Planing.project
                                                            ).options(selectinload(Project.section)
                                                            ).options(selectinload(Project.main_project)
                                                            ).options(selectinload(Project.sub_projects))
                                        ).options(selectinload(Planing.desa))
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_project_id_desa_id(
        self, *,
        project_id: UUID | str | None, 
        desa_id:UUID | str | None, 
        db_session: AsyncSession | None = None
    ) -> Planing:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Planing).where(and_(Planing.project_id == project_id, Planing.desa_id == desa_id)))
        return obj.scalar_one_or_none()
    
    async def create_planing(self, *, obj_in: PlaningCreateSch, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> Planing :
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