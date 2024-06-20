from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.dokumen_model import Dokumen
from schemas.dokumen_sch import DokumenCreateSch, DokumenUpdateSch
from typing import List
from uuid import UUID

class CRUDDokumen(CRUDBase[Dokumen, DokumenCreateSch, DokumenUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Dokumen | None:
        
        db_session = db_session or db.session
        
        query = select(Dokumen).where(Dokumen.id == id).options(selectinload(Dokumen.kategori_dokumen))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_name(self, 
                  *, 
                  name: str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Dokumen | None:
        
        db_session = db_session or db.session
        
        query = select(Dokumen).where(and_(Dokumen.name == name, Dokumen.is_active == True)
                            ).options(selectinload(Dokumen.kategori_dokumen)).limit(1)

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    async def is_dokumen_for_keyword(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> Dokumen | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.id == id, self.model.is_keyword == True))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

dokumen = CRUDDokumen(Dokumen)