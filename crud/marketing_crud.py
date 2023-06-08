from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.marketing_model import Manager, Sales
from schemas.marketing_sch import ManagerCreateSch, ManagerUpdateSch, SalesCreateSch, SalesUpdateSch
from typing import List
from uuid import UUID


class CRUDManager(CRUDBase[Manager, ManagerCreateSch, ManagerUpdateSch]):
    pass

manager = CRUDManager(Manager)


class CRUDSales(CRUDBase[Sales, SalesCreateSch, SalesUpdateSch]):
    pass

sales = CRUDSales(Sales)