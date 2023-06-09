from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.master_model import BebanBiaya
from schemas.beban_biaya_sch import BebanBiayaSch, BebanBiayaCreateSch, BebanBiayaUpdateSch
from typing import List
from uuid import UUID

class CRUDBebanBiaya(CRUDBase[BebanBiaya, BebanBiayaCreateSch, BebanBiayaUpdateSch]):
    pass

bebanbiaya = CRUDBebanBiaya(BebanBiaya)