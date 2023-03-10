from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.desa_model import Desa
from schemas.desa_sch import DesaCreateSch, DesaUpdateSch

class CRUDDesa(CRUDBase[Desa, DesaCreateSch, DesaUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> Desa:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Desa).where(Desa.name == name))
        return obj.scalar_one_or_none()

desa = CRUDDesa(Desa)