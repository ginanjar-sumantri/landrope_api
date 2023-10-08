from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import Payment, PaymentDetail, Invoice, Termin
from schemas.payment_sch import PaymentCreateSch, PaymentUpdateSch
from uuid import UUID

class CRUDPayment(CRUDBase[Payment, PaymentCreateSch, PaymentUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Payment | None:
        
        db_session = db_session or db.session
        
        query = select(Payment).where(Payment.id == id
                                ).options(selectinload(Payment.giro)
                                ).options(selectinload(Payment.details
                                                    ).options(selectinload(PaymentDetail.invoice
                                                                        ).options(selectinload(Invoice.bidang)
                                                                        ).options(selectinload(Invoice.termin
                                                                                            ).options(selectinload(Termin.tahap))
                                                                        )
                                                    )
                                )
                                    
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

payment = CRUDPayment(Payment)