from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import InvoiceDetail, Invoice, BidangKomponenBiaya, Termin
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from typing import List
from uuid import UUID

class CRUDInvoiceDetail(CRUDBase[InvoiceDetail, InvoiceDetailCreateSch, InvoiceDetailUpdateSch]):
    async def get_multi_by_ids_not_in(self, 
                            *,
                            invoice_id:UUID | None = None,
                            list_ids:List[UUID] | None = None,
                            db_session : AsyncSession | None = None
                            ) -> List[InvoiceDetail] | None:
        
        db_session = db_session or db.session

        query = select(self.model).where(and_(~self.model.id.in_(id for id in list_ids), self.model.invoice_id == invoice_id))

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_by_invoice_ids(self, 
                            *,
                            list_ids:List[UUID] | None = None,
                            beban_biaya_id:UUID,
                            termin_id:UUID,
                            db_session : AsyncSession | None = None
                            ) -> List[InvoiceDetail] | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                                    ).join(BidangKomponenBiaya, BidangKomponenBiaya.id == InvoiceDetail.bidang_komponen_biaya_id
                                    ).join(Termin, Termin.id == Invoice.termin_id
                                    ).where(and_(Invoice.id.in_(list_ids)),
                                                BidangKomponenBiaya.beban_biaya_id == beban_biaya_id,
                                                BidangKomponenBiaya.beban_pembeli == True,
                                                Termin.id == termin_id
                                                ).distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()

invoice_detail = CRUDInvoiceDetail(InvoiceDetail)