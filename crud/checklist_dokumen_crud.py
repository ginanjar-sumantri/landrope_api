from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import ChecklistDokumen, Dokumen
from schemas.checklist_dokumen_sch import ChecklistDokumenCreateSch, ChecklistDokumenUpdateSch
from typing import List
from uuid import UUID
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum

class CRUDChecklistDokumen(CRUDBase[ChecklistDokumen, ChecklistDokumenCreateSch, ChecklistDokumenUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  query : ChecklistDokumen | Select[ChecklistDokumen] | None = None,
                  db_session: AsyncSession | None = None
                  ) -> ChecklistDokumen | None:
        
        db_session = db_session or db.session

        if query == None:
            query = select(self.model).where(self.model.id == id
                                            ).options(selectinload(ChecklistDokumen.dokumen
                                                                ).options(selectinload(Dokumen.kategori_dokumen))
                                            )

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    async def get_single(self, *, 
                  dokumen_id: UUID | str,
                  jenis_alashak: JenisAlashakEnum,
                  jenis_bayar: JenisBayarEnum,
                  kategori_penjual: KategoriPenjualEnum,
                  db_session: AsyncSession | None = None) -> ChecklistDokumen | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.dokumen_id == dokumen_id, 
                                              self.model.jenis_alashak == jenis_alashak,
                                              self.model.jenis_bayar == jenis_bayar,
                                              self.model.kategori_penjual == kategori_penjual))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_by_jenis_alashak_and_kategori_penjual(
            self, 
            *,
            jenis_alashak:JenisAlashakEnum,
            kategori_penjual:KategoriPenjualEnum,
            db_session : AsyncSession | None = None) -> List[ChecklistDokumen] | None:
        
        db_session = db_session or db.session

        query = select(self.model).join(ChecklistDokumen.dokumen).where(
                                        and_(
                                            self.model.jenis_alashak == jenis_alashak,
                                            self.model.kategori_penjual == kategori_penjual),
                                            Dokumen.is_active != False
                                            )
        
        query = query.options(selectinload(self.model.dokumen))
        
        response =  await db_session.execute(query)
        return response.scalars().all()

checklistdokumen = CRUDChecklistDokumen(ChecklistDokumen)