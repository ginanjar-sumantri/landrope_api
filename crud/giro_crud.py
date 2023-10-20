from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from fastapi_async_sqlalchemy import db
from crud.base_crud import CRUDBase
from models import Giro, Payment
from schemas.giro_sch import GiroCreateSch, GiroUpdateSch
from uuid import UUID

class CRUDGiro(CRUDBase[Giro, GiroCreateSch, GiroUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Giro | None:
        
        db_session = db_session or db.session
        
        query = select(Giro).where(Giro.id == id
                                ).options(selectinload(Giro.payment))
                                    
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_nomor_giro(
        self, *, nomor_giro: str, db_session: AsyncSession | None = None
    ) -> Giro:
        db_session = db_session or db.session
        query = select(Giro).where(Giro.nomor_giro == nomor_giro)
        query = query.options(selectinload(Giro.payment
                                        ).options(selectinload(Payment.details))
                            )
        
        obj = await db_session.execute(query)
        return obj.scalar_one_or_none()

giro = CRUDGiro(Giro)