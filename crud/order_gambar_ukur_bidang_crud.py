from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from typing import List
from crud.base_crud import CRUDBase
from models.order_gambar_ukur_model import OrderGambarUkurBidang
from schemas.order_gambar_ukur_bidang_sch import OrderGambarUkurBidangCreateSch, OrderGambarUkurBidangUpdateSch
from uuid import UUID

class CRUDOrderGambarUkurBidang(CRUDBase[OrderGambarUkurBidang, OrderGambarUkurBidangCreateSch, OrderGambarUkurBidangUpdateSch]):
    async def get_not_in_by_kjb_dt_ids(self, *, order_ukur_id:UUID, list_ids: List[UUID | str], db_session : AsyncSession | None = None) -> List[OrderGambarUkurBidang] | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(~self.model.kjb_dt_id.in_(list_ids),
                                              self.model.order_gambar_ukur_id == order_ukur_id))
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_by_kjb_dt_id_and_order_ukur_id(self, *, kjb_dt_id: UUID | str, order_ukur_id: UUID | str, db_session: AsyncSession | None = None) -> OrderGambarUkurBidang | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.order_gambar_ukur_id == order_ukur_id, self.model.kjb_dt_id == kjb_dt_id))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

order_gambar_ukur_bidang = CRUDOrderGambarUkurBidang(OrderGambarUkurBidang)