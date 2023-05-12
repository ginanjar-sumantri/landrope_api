from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from crud.base_crud import CRUDBase
from models.desa_model import Desa
from schemas.desa_sch import DesaCreateSch, DesaUpdateSch, DesaSch
from geoalchemy2.shape import to_shape
from typing import List
from sqlalchemy.orm import load_only
from uuid import UUID

from datetime import datetime

class CRUDDesa(CRUDBase[Desa, DesaCreateSch, DesaUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> DesaCreateSch:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Desa).where(Desa.name == name))
        return obj.scalar_one_or_none()
    
    async def get_by_names(self, *, list_names: List[str], db_session : AsyncSession | None = None) -> List[DesaCreateSch] | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.name.in_(list_names))
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_all_(self, *, db_session : AsyncSession | None = None) -> List[DesaSch] | None:
        db_session = db_session or db.session
        query = select(self.model)
        response =  await db_session.execute(query)
        return response.scalars().all()

    
desa = CRUDDesa(Desa)