from crud.base_crud import CRUDBase
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from models.master_model import HargaStandard
from models.planing_model import Planing
from schemas.harga_standard_sch import HargaStandardCreateSch, HargaStandardUpdateSch
from common.enum import JenisAlashakEnum
from sqlmodel import select, and_
from uuid import UUID
from decimal import Decimal


class CRUDHargaStandard(CRUDBase[HargaStandard, HargaStandardCreateSch, HargaStandardUpdateSch]):
    async def get_by_planing_id_jenis_alashak(self, *, id:UUID|None = None, planing_id: UUID | str, jenis_alashak:JenisAlashakEnum|None=None,
                                            db_session: AsyncSession | None = None) -> HargaStandard | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.planing_id == planing_id, HargaStandard.jenis_alashak == jenis_alashak))
        if id:
            query = query.filter(HargaStandard.id != id)
            
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_desa_id(self, *, desa_id: UUID | str, db_session: AsyncSession | None = None) -> list[HargaStandard] | None:
        db_session = db_session or db.session
        query = select(HargaStandard
                    ).outerjoin(Planing, Planing.id == HargaStandard.planing_id
                    ).where(Planing.desa_id == desa_id).order_by(HargaStandard.harga.asc())
        
        response = await db_session.execute(query)

        return response.scalars().all()

harga_standard = CRUDHargaStandard(HargaStandard)