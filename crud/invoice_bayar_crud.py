from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.invoice_model import InvoiceBayar
from schemas.invoice_bayar_sch import InvoiceBayarCreateSch, InvoiceBayarlUpdateSch
from typing import List
from uuid import UUID

class CRUDInvoiceBayar(CRUDBase[InvoiceBayar, InvoiceBayarCreateSch, InvoiceBayarlUpdateSch]):
    pass

invoice_bayar = CRUDInvoiceBayar(InvoiceBayar)