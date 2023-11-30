from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import UtjKhususDetail, Invoice, Termin
from schemas.utj_khusus_detail_sch import UtjKhususDetailCreateSch, UtjKhususDetailUpdateSch
from uuid import UUID
from typing import List

class CRUDUtjKhususDetail(CRUDBase[UtjKhususDetail, UtjKhususDetailCreateSch, UtjKhususDetailUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> UtjKhususDetail | None:
        
        db_session = db_session or db.session
        
        query = select(UtjKhususDetail).where(UtjKhususDetail.id == id
                                ).options(selectinload(UtjKhususDetail.utj_khusus)
                                ).options(selectinload(UtjKhususDetail.kjb_dt)
                                ).options(selectinload(UtjKhususDetail.invoice
                                                ).options(selectinload(Invoice.payment_details)
                                                ).options(selectinload(Invoice.termin))
                                )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_kjb_dt_id(self, 
                  *, 
                  kjb_dt_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> UtjKhususDetail | None:
        
        db_session = db_session or db.session
        
        query = select(UtjKhususDetail).where(UtjKhususDetail.kjb_dt_id == kjb_dt_id
                                ).options(selectinload(UtjKhususDetail.utj_khusus)
                                ).options(selectinload(UtjKhususDetail.kjb_dt)
                                ).options(selectinload(UtjKhususDetail.invoice
                                                ).options(selectinload(Invoice.payment_details)
                                                ).options(selectinload(Invoice.termin))
                                )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_not_in_id_removed(self, *, list_ids: List[UUID | str], utj_khusus_id:UUID, db_session : AsyncSession | None = None
                                ) -> List[UtjKhususDetail] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(~self.model.id.in_(list_ids), 
                                              self.model.utj_khusus_id == utj_khusus_id)
                                              ).options(selectinload(UtjKhususDetail.invoice
                                                                ).options(selectinload(Invoice.payment_details))
                                                )
        
        response =  await db_session.execute(query)
        return response.scalars().all()

utj_khusus_detail = CRUDUtjKhususDetail(UtjKhususDetail)