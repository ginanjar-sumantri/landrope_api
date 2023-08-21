from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumenDt
from schemas.checklist_kelengkapan_dokumen_dt_sch import ChecklistKelengkapanDokumenDtCreateSch, ChecklistKelengkapanDokumenDtExtSch, ChecklistKelengkapanDokumenDtUpdateSch
from typing import List
from uuid import UUID
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum

class CRUDChecklistKelengkapanDokumenDt(CRUDBase[ChecklistKelengkapanDokumenDt, ChecklistKelengkapanDokumenDtCreateSch, ChecklistKelengkapanDokumenDtUpdateSch]):
    async def get_all(self, 
                      *, 
                      db_session : AsyncSession | None = None,
                      query : Select[ChecklistKelengkapanDokumenDt] | None = None) -> List[ChecklistKelengkapanDokumenDtExtSch] | None:
        
        db_session = db_session or db.session

        if query is None:
            query = select(self.model)
            
        response =  await db_session.execute(query)
        return response.scalars().all()

checklist_kelengkapan_dokumen_dt = CRUDChecklistKelengkapanDokumenDt(ChecklistKelengkapanDokumenDt)