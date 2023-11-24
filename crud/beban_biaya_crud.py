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
    async def get_beban_biaya_add_pay(self, *,
                    list_id:list[UUID]|None = [],
                    db_session : AsyncSession | None = None
                    ) -> List[BebanBiaya] | None:
        
        db_session = db_session or db.session
        if query is None:
            query = select(self.model).where(and_(BebanBiaya.id.in_(list_id), BebanBiaya.is_add_pay == True))

        response =  await db_session.execute(query)
        return response.scalars().all()

bebanbiaya = CRUDBebanBiaya(BebanBiaya)