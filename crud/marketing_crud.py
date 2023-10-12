from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import Manager, Sales, Bidang
from schemas.marketing_sch import ManagerCreateSch, ManagerUpdateSch, SalesCreateSch, SalesUpdateSch
from typing import List
from uuid import UUID


class CRUDManager(CRUDBase[Manager, ManagerCreateSch, ManagerUpdateSch]):
    async def get_multi_by_bidang_ids(self, 
                        list_ids: List[UUID | str], 
                        db_session : AsyncSession | None = None
                        ) -> List[Manager]:
        
        db_session = db_session or db.session

        query = select(Manager)
        query = query.join(Bidang, Bidang.manager_id == Manager.id)
        query = query.filter(Bidang.id.in_(list_ids))
        query = query.distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()

manager = CRUDManager(Manager)


class CRUDSales(CRUDBase[Sales, SalesCreateSch, SalesUpdateSch]):
    async def get_multi_by_bidang_ids(self, 
                        list_ids: List[UUID | str], 
                        db_session : AsyncSession | None = None
                        ) -> List[Sales]:
        
        db_session = db_session or db.session

        query = select(Sales)
        query = query.join(Bidang, Bidang.sales_id == Sales.id)
        query = query.filter(Bidang.id.in_(list_ids))
        query = query.distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()

sales = CRUDSales(Sales)