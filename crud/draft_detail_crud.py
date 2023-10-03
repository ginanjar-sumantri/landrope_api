from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.draft_model import DraftDetail
from schemas.draft_detail_sch import DraftDetailCreateSch, DraftDetailUpdateSch
from uuid import UUID

class CRUDDraftDetail(CRUDBase[DraftDetail, DraftDetailCreateSch, DraftDetailUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> DraftDetail | None:
        
        db_session = db_session or db.session
        
        query = select(DraftDetail).where(DraftDetail.id == id
                                        ).options(selectinload(DraftDetail.draft)
                                        ).options(selectinload(DraftDetail.bidang))
                                                    

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def remove_multiple_data(self, *, list_obj: list[DraftDetail],
                                   db_session: AsyncSession | None = None) -> None:
        db_session = db.session or db_session
        for i in list_obj:
            await db_session.delete(i)

draft_detail = CRUDDraftDetail(DraftDetail)