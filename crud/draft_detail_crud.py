from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.draft_model import DraftDetail
from schemas.draft_detail_sch import DraftDetailCreateSch, DraftDetailUpdateSch

class CRUDDraftDetail(CRUDBase[DraftDetail, DraftDetailCreateSch, DraftDetailUpdateSch]):
    pass

draft_detail = CRUDDraftDetail(DraftDetail)