from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.payment_model import PaymentGiroDetail
from schemas.payment_giro_detail_sch import PaymentGiroDetailCreateSch, PaymentGiroDetailUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDPaymentGiroDetail(CRUDBase[PaymentGiroDetail, PaymentGiroDetailCreateSch, PaymentGiroDetailUpdateSch]):
    pass

payment_giro_detail = CRUDPaymentGiroDetail(PaymentGiroDetail)