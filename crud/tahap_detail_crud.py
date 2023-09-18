from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.tahap_model import TahapDetail
from schemas.tahap_detail_sch import TahapDetailCreateSch, TahapDetailUpdateSch
from typing import List
from uuid import UUID

class CRUDTahapDetail(CRUDBase[TahapDetail, TahapDetailCreateSch, TahapDetailUpdateSch]):
   async def get_multi_removed_detail(
           self, 
           *, 
           list_ids: List[UUID | str],
           tahap_id:UUID | str,
           db_session : AsyncSession | None = None) -> List[TahapDetail] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(
            and_(
            ~self.model.id.in_(list_ids),
            self.model.tahap_id == tahap_id,
            self.model.is_void == False
        ))
        response =  await db_session.execute(query)
        return response.scalars().all()

tahap_detail = CRUDTahapDetail(TahapDetail)