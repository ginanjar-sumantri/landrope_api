from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import InvoiceBayar, Invoice, Bidang, InvoiceDetail, BidangKomponenBiaya
from schemas.invoice_bayar_sch import InvoiceBayarCreateSch, InvoiceBayarlUpdateSch
from typing import List
from uuid import UUID

class CRUDInvoiceBayar(CRUDBase[InvoiceBayar, InvoiceBayarCreateSch, InvoiceBayarlUpdateSch]):
    async def get_multi_by_termin_id(self, 
                  *, 
                  termin_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[InvoiceBayar] | None:
        
        db_session = db_session or db.session
        
        query = select(InvoiceBayar).join(InvoiceBayar.invoice)

        query = query.filter(Invoice.termin_id == termin_id)
        query = query.filter(Invoice.is_void != True)

        query = query.options(selectinload(InvoiceBayar.invoice)
                    ).options(selectinload(InvoiceBayar.termin_bayar))
        
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
    #for termin update function
    async def get_ids_by_invoice_ids(self, 
                            *,
                            list_ids:List[UUID] | None = None,
                            db_session : AsyncSession | None = None
                            ) -> List[UUID] | None:
        
        db_session = db_session or db.session

        query = select(InvoiceBayar).where(InvoiceBayar.invoice_id.in_(list_ids))

        response =  await db_session.execute(query)
        result = response.scalars().all()
        
        datas = [data.id for data in result]
        return datas

invoice_bayar = CRUDInvoiceBayar(InvoiceBayar)