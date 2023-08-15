from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch

from crud.base_crud import CRUDBase
from models.bidang_model import Bidangoverlap
from schemas.bidang_overlap_sch import BidangOverlapCreateSch, BidangOverlapUpdateSch

class CRUDBidangOverlap(CRUDBase[Bidangoverlap, BidangOverlapCreateSch, BidangOverlapUpdateSch]):
    pass

bidangoverlap = CRUDBidangOverlap(Bidangoverlap)