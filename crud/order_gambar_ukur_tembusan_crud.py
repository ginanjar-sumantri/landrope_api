from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from typing import List
from crud.base_crud import CRUDBase
from models.order_gambar_ukur_model import OrderGambarUkurTembusan
from schemas.order_gambar_ukur_tembusan_sch import OrderGambarUkurTembusanCreateSch, OrderGambarUkurTembusanUpdateSch
from uuid import UUID


class CRUDOrderGambarUkurTembusan(CRUDBase[OrderGambarUkurTembusan, OrderGambarUkurTembusanCreateSch, OrderGambarUkurTembusanUpdateSch]):
     async def get_not_in_by_tembusan_ids(self, *, order_ukur_id:UUID, list_ids: List[UUID | str], db_session : AsyncSession | None = None) -> List[OrderGambarUkurTembusan] | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(~self.model.tembusan_id.in_(list_ids),
                                              self.model.order_gambar_ukur_id == order_ukur_id))
        response =  await db_session.execute(query)
        return response.scalars().all()
     
     async def get_by_tembusan_id_and_order_ukur_id(self, *, tembusan_id: UUID | str, order_ukur_id: UUID | str, db_session: AsyncSession | None = None) -> OrderGambarUkurTembusan | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.order_gambar_ukur_id == order_ukur_id, self.model.tembusan_id == tembusan_id))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

order_gambar_ukur_tembusan = CRUDOrderGambarUkurTembusan(OrderGambarUkurTembusan)