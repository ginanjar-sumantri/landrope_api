from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import TandaTerimaNotarisDt, Dokumen
from schemas.tanda_terima_notaris_dt_sch import TandaTerimaNotarisDtCreateSch, TandaTerimaNotarisDtUpdateSch
from typing import List
from uuid import UUID

class CRUDTandaTerimaNotarisDt(CRUDBase[TandaTerimaNotarisDt, TandaTerimaNotarisDtCreateSch, TandaTerimaNotarisDtUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> TandaTerimaNotarisDt | None:
        
        db_session = db_session or db.session
        
        query = select(TandaTerimaNotarisDt).where(TandaTerimaNotarisDt.id == id
                                                    ).options(selectinload(TandaTerimaNotarisDt.dokumen
                                                                            ).options(selectinload(Dokumen.kategori_dokumen))
                                                    ).options(selectinload(TandaTerimaNotarisDt.tanda_terima_notaris_hd))
                                                    

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

tandaterimanotaris_dt = CRUDTandaTerimaNotarisDt(TandaTerimaNotarisDt)