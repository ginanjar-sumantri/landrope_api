from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from typing import List
from crud.base_crud import CRUDBase
from models.order_gambar_ukur_model import OrderGambarUkurTembusan
from schemas.order_gambar_ukur_tembusan_sch import OrderGambarUkurTembusanCreateSch, OrderGambarUkurTembusanUpdateSch
from uuid import UUID


class CRUDOrderGambarUkurTembusan(CRUDBase[OrderGambarUkurTembusan, OrderGambarUkurTembusanCreateSch, OrderGambarUkurTembusanUpdateSch]):
     async def get_not_in_by_tembusan_ids(self, *, list_ids: List[UUID | str], db_session : AsyncSession | None = None) -> List[OrderGambarUkurTembusan] | None:
        db_session = db_session or db.session
        query = select(self.model).where(~self.model.tembusan_id.in_(list_ids))
        response =  await db_session.execute(query)
        return response.scalars().all()

order_gambar_ukur_tembusan = CRUDOrderGambarUkurTembusan(OrderGambarUkurTembusan)