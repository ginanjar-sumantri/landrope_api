from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import PaymentDetail, Payment, Invoice, Termin, Giro
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch, PaymentDetailForPrintout
from common.enum import JenisBayarEnum
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
        query = select(self.model).where(and_(~self.model.id.in_(list_ids), self.model.payment_id == payment_id)
                                ).options(selectinload(PaymentDetail.invoice
                                        ).options(selectinload(Invoice.termin)
                                        ).options(selectinload(Invoice.details))
                                )
        
        response = await db_session.execute(query)
        return response.scalars().all()
    
    async def get_payment_detail_by_bidang_id(self, *, 
                                    bidang_id:UUID, 
                                    db_session : AsyncSession | None = None
                                ) -> List[PaymentDetail] | None:
        
        db_session = db_session or db.session
        
        query = select(PaymentDetail)
        query = query.join(PaymentDetail.invoice)
        query = query.join(Invoice.termin)
        query = query.filter(PaymentDetail.is_void != True)
        query = query.filter(Invoice.bidang_id == bidang_id)
        query = query.filter(~Termin.jenis_bayar.in_([JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]))
        
        query = query.options(selectinload(PaymentDetail.invoice
                                        ).options(selectinload(Invoice.termin)
                                        ).options(selectinload(Invoice.details))
                                )

        response =  await db_session.execute(query)
        return response.scalars().all()
    # pass

payment_detail = CRUDPaymentDetail(PaymentDetail)