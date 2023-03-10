from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.bidang_model import Bidangoverlap
from schemas.bidangoverlap_sch import BidangoverlapCreateSch, BidangoverlapUpdateSch

class CRUDBidangOverlap(CRUDBase[Bidangoverlap, BidangoverlapCreateSch, BidangoverlapUpdateSch]):
    async def get_by_id_bidang(
        self, *, idbidang: str, db_session: AsyncSession | None = None
    ) -> Bidangoverlap:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidangoverlap).where(Bidangoverlap.id_bidang == idbidang))
        return obj.scalar_one_or_none()

bidangoverlap = CRUDBidangOverlap(Bidangoverlap)