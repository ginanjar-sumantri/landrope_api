from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.tanda_terima_notaris_model import TandaTerimaNotarisDt
from schemas.tanda_terima_notaris_dt_sch import TandaTerimaNotarisDtCreateSch, TandaTerimaNotarisDtUpdateSch
from typing import List
from uuid import UUID

class CRUDTandaTerimaNotarisDt(CRUDBase[TandaTerimaNotarisDt, TandaTerimaNotarisDtCreateSch, TandaTerimaNotarisDtUpdateSch]):
    pass

tandaterimanotaris_dt = CRUDTandaTerimaNotarisDt(TandaTerimaNotarisDt)