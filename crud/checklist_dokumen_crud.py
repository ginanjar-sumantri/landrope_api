from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.checklist_dokumen_model import ChecklistDokumen
from schemas.checklist_dokumen_sch import ChecklistDokumenCreateSch, ChecklistDokumenUpdateSch
from typing import List
from uuid import UUID
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum

class CRUDChecklistDokumen(CRUDBase[ChecklistDokumen, ChecklistDokumenCreateSch, ChecklistDokumenUpdateSch]):
    async def get(self, *, 
                  dokumen_id: UUID | str,
                  jenis_alashak: JenisAlashakEnum,
                  jenis_bayar: JenisBayarEnum,
                  kategori_penjual: KategoriPenjualEnum,
                  db_session: AsyncSession | None = None) -> ChecklistDokumen | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.dokumen_id == id, 
                                              self.model.jenis_alashak == jenis_alashak,
                                              self.model.jenis_bayar == jenis_bayar,
                                              self.model.kategori_penjual == kategori_penjual))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

checklistdokumen = CRUDChecklistDokumen(ChecklistDokumen)