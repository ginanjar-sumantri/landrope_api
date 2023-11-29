from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import UtjKhusus
from schemas.utj_khusus_sch import UtjKhususCreateSch, UtjKhususUpdateSch
from uuid import UUID

class CRUDUtjKhusus(CRUDBase[UtjKhusus, UtjKhususCreateSch, UtjKhususUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> UtjKhusus | None:
        
        db_session = db_session or db.session
        
        query = select(UtjKhusus).where(UtjKhusus.id == id
                                ).options(selectinload(UtjKhusus.kjb_hd)
                                ).options(selectinload(UtjKhusus.payment))
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

utj_khusus = CRUDUtjKhusus(UtjKhusus)