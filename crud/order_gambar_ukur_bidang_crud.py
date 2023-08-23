from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from typing import List
from crud.base_crud import CRUDBase
from models.order_gambar_ukur_model import OrderGambarUkurBidang
from schemas.order_gambar_ukur_bidang_sch import OrderGambarUkurBidangCreateSch, OrderGambarUkurBidangUpdateSch
from uuid import UUID

class CRUDOrderGambarUkurBidang(CRUDBase[OrderGambarUkurBidang, OrderGambarUkurBidangCreateSch, OrderGambarUkurBidangUpdateSch]):
    async def get_not_in_by_bidang_ids(self, *, list_ids: List[UUID | str], db_session : AsyncSession | None = None) -> List[OrderGambarUkurBidang] | None:
        db_session = db_session or db.session
        query = select(self.model).where(~self.model.bidang_id.in_(list_ids))
        response =  await db_session.execute(query)
        return response.scalars().all()

order_gambar_ukur_bidang = CRUDOrderGambarUkurBidang(OrderGambarUkurBidang)