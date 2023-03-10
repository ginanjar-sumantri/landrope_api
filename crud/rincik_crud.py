from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.rincik_model import Rincik
from schemas.rincik_sch import RincikCreateSch, RincikUpdateSch

class CRUDRincik(CRUDBase[Rincik, RincikCreateSch, RincikUpdateSch]):
    async def get_by_id_rincik(
        self, *, idrincik: str, db_session: AsyncSession | None = None
    ) -> Rincik:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Rincik).where(Rincik.id_rincik == idrincik))
        return obj.scalar_one_or_none()

rincik = CRUDRincik(Rincik)