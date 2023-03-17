from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.planing_model import Planing
from schemas.planing_sch import PlaningCreateSch, PlaningUpdateSch

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
        obj = await db_session.execute(select(Planing).filter(Planing.project_id == project_id and Planing.desa_id == desa_id))
        return obj.scalar_one_or_none()

planing = CRUDPlaning(Planing)