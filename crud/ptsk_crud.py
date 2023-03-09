from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.ptsk_model import PTSK
from schemas.ptsk_sch import PTSKCreateSch, PTSKUpdateSch

class CRUDPTSK(CRUDBase[PTSK, PTSKCreateSch, PTSKUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> PTSK:
        db_session = db_session or db.session
        obj = await db_session.execute(select(PTSK).where(PTSK.name == name))
        return obj.scalar_one_or_none()

ptsk = CRUDPTSK(PTSK)