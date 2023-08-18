from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumen
from schemas.checklist_kelengkapan_dokumen_sch import ChecklistKelengkapanDokumenCreateSch, ChecklistKelengkapanDokumenUpdateSch
from typing import List
from uuid import UUID
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum

class CRUDChecklistKelengkapanDokumen(CRUDBase[ChecklistKelengkapanDokumen, ChecklistKelengkapanDokumenCreateSch, ChecklistKelengkapanDokumenUpdateSch]):
    pass

checklistkelengkapandokumen = CRUDChecklistKelengkapanDokumen(ChecklistKelengkapanDokumen)