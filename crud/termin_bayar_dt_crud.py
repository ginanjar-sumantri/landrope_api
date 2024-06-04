from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import TerminBayarDt
from schemas.termin_bayar_dt_sch import TerminBayarDtCreateSch, TerminBayarDtUpdateSch
from typing import List
from uuid import UUID


class CRUDTerminBayarDt(CRUDBase[TerminBayarDt, TerminBayarDtCreateSch, TerminBayarDtUpdateSch]):
    pass


termin_bayar_dt = CRUDTerminBayarDt(TerminBayarDt)
