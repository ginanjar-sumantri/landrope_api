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

class CRUDChecklistDokumen(CRUDBase[ChecklistDokumen, ChecklistDokumenCreateSch, ChecklistDokumenUpdateSch]):
    pass

checklistdokumen = CRUDChecklistDokumen(ChecklistDokumen)