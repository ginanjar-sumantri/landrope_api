from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from crud.base_crud import CRUDBase
from models.desa_model import Desa
from schemas.desa_sch import DesaCreateSch, DesaUpdateSch
from geoalchemy2.shape import to_shape

from datetime import datetime

class CRUDDesa(CRUDBase[Desa, DesaCreateSch, DesaUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> DesaCreateSch:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Desa).where(Desa.name == name))
        return obj.scalar_one_or_none()
    
    async def create_desa(self, db_session: AsyncSession | None = None, **kwargs) -> Desa:
        db_session = db_session or db.session
        db_obj = self.model(**kwargs)
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()

        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)

        if db_obj.geom :
            db_obj.geom = to_shape(db_obj.geom).__str__()
            
        return db_obj


desa = CRUDDesa(Desa)