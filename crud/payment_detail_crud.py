from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, func
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import PaymentDetail, Payment, Invoice, Termin, Giro
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch, PaymentDetailForPrintout
from uuid import UUID
from typing import List

class CRUDPaymentDetail(CRUDBase[PaymentDetail, PaymentDetailCreateSch, PaymentDetailUpdateSch]):
    async def get_by_termin_id_for_printout(self, *, 
                  termin_id: UUID | str,
                  db_session: AsyncSession | None = None
                  ) -> list[PaymentDetailForPrintout] | None:
        
        db_session = db_session or db.session
        query = select(func.sum(PaymentDetail.amount).label("amount"),
                       Payment.payment_method,
                       Payment.pay_to,
                       Giro.code).join(Invoice, Invoice.id == PaymentDetail.invoice_id
                                ).join(Termin, Termin.id == Invoice.termin_id
                                ).join(Payment, Payment.id == PaymentDetail.payment_id
                                ).outerjoin(Giro, Giro.id == Payment.giro_id
                                ).where(
                                    and_(
                                        Termin.id == termin_id,
                                        Invoice.is_void != True,
                                        PaymentDetail.is_void != True,
                                        Payment.is_void != True
                                        )
                                    ).group_by(Invoice.id, Payment.id, Giro.id)
        
        response = await db_session.execute(query)

        return response.fetchall()
    
    async def get_payment_not_in_by_ids(self, *, list_ids: List[UUID | str], payment_id:UUID, db_session : AsyncSession | None = None
                                ) -> List[PaymentDetail] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(~self.model.id.in_(list_ids), self.model.payment_id == payment_id))
        response =  await db_session.execute(query)
        return response.scalars().all()
    # pass

payment_detail = CRUDPaymentDetail(PaymentDetail)