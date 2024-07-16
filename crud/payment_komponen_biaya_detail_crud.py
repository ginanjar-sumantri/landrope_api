from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.payment_model import PaymentKomponenBiayaDetail
from schemas.payment_komponen_biaya_detail_sch import PaymentKomponenBiayaDetailCreateSch, PaymentKomponenBiayaDetailUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDPaymentKomponenBiayaDetail(CRUDBase[PaymentKomponenBiayaDetail, PaymentKomponenBiayaDetailCreateSch, PaymentKomponenBiayaDetailUpdateSch]):
    async def get_by_invoice_detail_id(self, 
                  *, 
                  invoice_detail_id: UUID | None = None,
                  db_session: AsyncSession | None = None
                  ) -> List[PaymentKomponenBiayaDetail] | None:
        
        db_session = db_session or db.session
        
        query = select(PaymentKomponenBiayaDetail).where(PaymentKomponenBiayaDetail.invoice_detail_id == invoice_detail_id)
        
        response = await db_session.execute(query)

        return response.scalars().all()

payment_komponen_biaya_detail = CRUDPaymentKomponenBiayaDetail(PaymentKomponenBiayaDetail)