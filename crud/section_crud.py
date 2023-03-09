from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.section_model import Section
from schemas.section_sch import SectionCreateSch, SectionUpdateSch

class CRUDSection(CRUDBase[Section, SectionCreateSch, SectionUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> Section:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Section).where(Section.name == name))
        return obj.scalar_one_or_none()

section = CRUDSection(Section)