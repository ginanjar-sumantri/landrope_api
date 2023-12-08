from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
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
    async def get_multi_by_bidang_ids_and_manager_id(self, 
                        list_ids: List[UUID | str],
                        manager_id:UUID | None = None, 
                        db_session : AsyncSession | None = None
                        ) -> List[Sales]:
        
        db_session = db_session or db.session

        query = select(Sales)
        query = query.join(Bidang, Bidang.sales_id == Sales.id)
        query = query.filter(Bidang.id.in_(list_ids))
        
        if manager_id:
            query = query.filter(Sales.manager_id == manager_id)

        query = query.distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  query : Sales | Select[Sales] | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Sales | None:
        
        db_session = db_session or db.session

        if query == None:
            query = select(self.model).where(self.model.id == id).options(selectinload(Sales.manager))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_name_and_manager_id(
        self, *, 
        name: str,
        manager_id:UUID, 
        db_session: AsyncSession | None = None
    ) -> Sales:
        
        db_session = db_session or db.session
        query = select(self.model)
        query = query.filter(func.lower(func.trim(func.replace(func.replace(self.model.name, ' ', ''), '-', ''))) == name.strip().lower().replace(' ', '').replace('-', ''))
        query = query.filter(Sales.manager_id == manager_id)

        obj = await db_session.execute(query)
        return obj.scalar_one_or_none()

sales = CRUDSales(Sales)