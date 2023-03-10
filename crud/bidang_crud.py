from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.bidang_model import Bidang
from schemas.bidang_sch import BidangCreateSch, BidangUpdateSch

class CRUDBidang(CRUDBase[Bidang, BidangCreateSch, BidangUpdateSch]):
    async def get_by_id_bidang(
        self, *, idbidang: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang == idbidang))
        return obj.scalar_one_or_none()

bidang = CRUDBidang(Bidang)