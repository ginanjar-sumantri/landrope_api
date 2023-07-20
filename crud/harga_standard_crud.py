from crud.base_crud import CRUDBase
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from models.master_model import HargaStandard
from models.planing_model import Planing
from schemas.harga_standard_sch import HargaStandardCreateSch, HargaStandardUpdateSch
from sqlmodel import select, and_
from uuid import UUID
from decimal import Decimal


class CRUDHargaStandard(CRUDBase[HargaStandard, HargaStandardCreateSch, HargaStandardUpdateSch]):
    async def get_by_planing_id(self, *, planing_id: UUID | str, db_session: AsyncSession | None = None) -> HargaStandard | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.planing_id == planing_id)
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_desa_id(self, *, desa_id: UUID | str, harga:Decimal, db_session: AsyncSession | None = None) -> HargaStandard | None:
        db_session = db_session or db.session
        query = select(self.model
        ).select_from(self.model
                      ).outerjoin(Planing, Planing.id == self.model.planing_id
                      ).where(Planing.desa_id == desa_id).order_by(self.model.harga.asc())
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

harga_standard = CRUDHargaStandard(HargaStandard)