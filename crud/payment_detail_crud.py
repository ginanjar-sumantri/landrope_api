from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import PaymentDetail, Payment, Invoice, Termin, Giro
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch, PaymentDetailForPrintout
from uuid import UUID

class CRUDPaymentDetail(CRUDBase[PaymentDetail, PaymentDetailCreateSch, PaymentDetailUpdateSch]):
    # async def get_by_termin_id_for_printout(self, *, 
    #               termin_id: UUID | str,
    #               db_session: AsyncSession | None = None
    #               ) -> list[PaymentDetailForPrintout] | None:
        
    #     db_session = db_session or db.session
    #     query = select(PaymentDetail).join(Invoice, Invoice.id == PaymentDetail.invoice_id
    #                             ).join(Termin, Spk.kjb_termin_id == KjbTermin.id
    #                             ).join(Invoice, Invoice.spk_id == Spk.id
    #                             ).join(Termin, Termin.id == Invoice.termin_id
    #                             ).where(Termin.id == termin_id).distinct()
        
    #     response = await db_session.execute(query)

    #     return response.fetchall()
    pass

payment_detail = CRUDPaymentDetail(PaymentDetail)