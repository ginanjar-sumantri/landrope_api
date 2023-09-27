from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.tanda_terima_notaris_model import TandaTerimaNotarisHd
from schemas.tanda_terima_notaris_hd_sch import TandaTerimaNotarisHdCreateSch, TandaTerimaNotarisHdUpdateSch, TandaTerimaNotarisHdForCloud
from typing import List
from uuid import UUID

class CRUDTandaTerimaNotarisHd(CRUDBase[TandaTerimaNotarisHd, TandaTerimaNotarisHdCreateSch, TandaTerimaNotarisHdUpdateSch]):
    async def get_one_by_kjb_dt_id(self, *, kjb_dt_id: UUID | str, db_session: AsyncSession | None = None) -> TandaTerimaNotarisHdForCloud | None:
        db_session = db_session or db.session
        query = select(self.model.id, self.model.notaris_id).where(self.model.kjb_dt_id == kjb_dt_id).order_by(self.model.created_at.desc())
        response = await db_session.execute(query)

        return response.fetchone()

tandaterimanotaris_hd = CRUDTandaTerimaNotarisHd(TandaTerimaNotarisHd)