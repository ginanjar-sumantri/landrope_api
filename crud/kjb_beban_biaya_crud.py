from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.kjb_model import KjbBebanBiaya
from schemas.kjb_beban_biaya_sch import KjbBebanBiayaCreateSch, KjbBebanBiayaUpdateSch, KjbBebanBiayaSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDKjbBebanBiaya(CRUDBase[KjbBebanBiaya, KjbBebanBiayaCreateSch, KjbBebanBiayaUpdateSch]):
    async def get_beban_pembeli_by_kjb_hd_id(self, *, 
                  kjb_hd_id: UUID | str,
                  db_session: AsyncSession | None = None) -> List[KjbBebanBiayaSch] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.kjb_hd_id == kjb_hd_id, self.model.beban_pembeli == True)
                                        ).options(selectinload(KjbBebanBiaya.beban_biaya))
        response = await db_session.execute(query)

        return response.scalars().all()

kjb_bebanbiaya = CRUDKjbBebanBiaya(KjbBebanBiaya)