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

        query = query.options(selectinload(InvoiceBayar.invoice
                                                ).options(selectinload(Invoice.spk)
                                                ).options(selectinload(Invoice.termin)
                                                ).options(selectinload(Invoice.bidang
                                                                        ).options(selectinload(Bidang.invoices
                                                                                        ).options(selectinload(Invoice.termin)
                                                                                        ).options(selectinload(Invoice.payment_details))
                                                                        )
                                                ).options(selectinload(Invoice.details
                                                                        ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                                        ).options(selectinload(BidangKomponenBiaya.bidang))
                                                                        )
                                                ).options(selectinload(Invoice.bayars)
                                                ).options(selectinload(Invoice.payment_details))
                    ).options(selectinload(InvoiceBayar.termin_bayar))
        
        
        response = await db_session.execute(query)

        return response.scalars().all()

invoice_bayar = CRUDInvoiceBayar(InvoiceBayar)