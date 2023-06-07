from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.master_model import JenisLahan
from schemas.jenis_lahan_sch import JenisLahanCreateSch, JenisLahanUpdateSch

class CRUDJenisLahan(CRUDBase[JenisLahan, JenisLahanCreateSch, JenisLahanUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> JenisLahan:
        db_session = db_session or db.session
        obj = await db_session.execute(select(JenisLahan).where(JenisLahan.name == name))
        return obj.scalar_one_or_none()

jenislahan = CRUDJenisLahan(JenisLahan)