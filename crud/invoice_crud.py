from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.invoice_model import Invoice
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch
from typing import List
from uuid import UUID

class CRUDInvoice(CRUDBase[Invoice, InvoiceCreateSch, InvoiceUpdateSch]):
    pass

invoice = CRUDInvoice(Invoice)