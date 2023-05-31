from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.dokumen_model import Dokumen
from schemas.dokumen_sch import DokumenCreateSch, DokumenUpdateSch
from typing import List
from uuid import UUID

class CRUDDokumen(CRUDBase[Dokumen, DokumenCreateSch, DokumenUpdateSch]):
    async def is_dokumen_for_keyword(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> Dokumen | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.id == id, self.model.is_keyword == True))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

dokumen = CRUDDokumen(Dokumen)