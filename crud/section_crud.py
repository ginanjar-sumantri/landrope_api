from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.section_model import Section
from schemas.section_sch import SectionCreateSch, SectionUpdateSch

class CRUDSection(CRUDBase[Section, SectionCreateSch, SectionUpdateSch]):
    pass

section = CRUDSection(Section)