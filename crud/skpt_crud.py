from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.skpt_model import Skpt
from schemas.skpt_sch import SkptCreateSch, SkptUpdateSch
from typing import List
from uuid import UUID

class CRUDSKPT(CRUDBase[Skpt, SkptCreateSch, SkptUpdateSch]):
    async def get_by_sk_number(
        self, *, number: str, db_session: AsyncSession | None = None
    ) -> Skpt:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Skpt).where(Skpt.nomor_sk == number).limit(1))
        return obj.scalar_one_or_none()
    
    async def get_by_ptsk_id(
        self, *, ptsk_id: UUID | None, db_session: AsyncSession | None = None
    ) -> List[Skpt]:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Skpt).where(Skpt.ptsk_id == ptsk_id))
        return obj.scalar_one_or_none()
    
    async def get_by_sk_number_and_ptsk_id(
        self, *, no_sk: str, ptsk_id:UUID | None, db_session: AsyncSession | None = None
    ) -> Skpt:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Skpt).where(and_(Skpt.nomor_sk == no_sk, Skpt.ptsk_id == ptsk_id)).limit(1))
        return obj.scalar_one_or_none()
    

skpt = CRUDSKPT(Skpt)