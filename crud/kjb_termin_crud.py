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
from models.kjb_model import KjbTermin
from schemas.kjb_termin_sch import KjbTerminCreateSch, KjbTerminUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc
import crud



class CRUDKjbTermin(CRUDBase[KjbTermin, KjbTerminCreateSch, KjbTerminUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> KjbTermin | None:
        
        db_session = db_session or db.session
        
        query = select(KjbTermin).where(KjbTermin.id == id
                                                ).options(selectinload(KjbTermin.harga))
                                                

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_by_kjb_harga_id(self, 
                  *, 
                  kjb_harga_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[KjbTermin] | None:
        
        db_session = db_session or db.session
        
        query = select(KjbTermin).where(KjbTermin.kjb_harga_id == kjb_harga_id
                                                ).options(selectinload(KjbTermin.harga))
                                                

        response = await db_session.execute(query)

        return response.scalars().all()

kjb_termin = CRUDKjbTermin(KjbTermin)