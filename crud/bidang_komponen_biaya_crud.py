from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.bidang_komponen_biaya_model import BidangKomponenBiaya
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch
from typing import List
from uuid import UUID

class CRUDBidangKomponenBiaya(CRUDBase[BidangKomponenBiaya, BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch]):
    async def get_by_bidang_id_and_beban_biaya_id(
            self, 
            *, 
            bidang_id: UUID | str, 
            beban_biaya_id: UUID | str, 
            db_session: AsyncSession | None = None) -> BidangKomponenBiaya | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(
                            self.model.bidang_id == bidang_id,
                            self.model.beban_biaya_id == beban_biaya_id
            ))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiaya] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(self.model.bidang_id == bidang_id)
        response = await db_session.execute(query)

        return response.scalars().all()

bidang_komponen_biaya = CRUDBidangKomponenBiaya(BidangKomponenBiaya)