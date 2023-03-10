from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.ptsk_model import Ptsk
from schemas.ptsk_sch import PtskCreateSch, PtskUpdateSch

class CRUDPTSK(CRUDBase[Ptsk, PtskCreateSch, PtskUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> Ptsk:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Ptsk).where(Ptsk.name == name))
        return obj.scalar_one_or_none()

ptsk = CRUDPTSK(Ptsk)