from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from fastapi_async_sqlalchemy import db
from crud.base_crud import CRUDBase
from models import Notaris, Bidang
from schemas.notaris_sch import NotarisCreateSch, NotarisUpdateSch
from typing import List
from uuid import UUID


class CRUDNotaris(CRUDBase[Notaris, NotarisCreateSch, NotarisUpdateSch]):
    async def get_multi_by_bidang_ids(self, 
                        list_ids: List[UUID | str], 
                        db_session : AsyncSession | None = None
                        ) -> List[Notaris]:
        
        db_session = db_session or db.session

        query = select(Notaris)
        query = query.join(Bidang, Bidang.notaris_id == Notaris.id)
        query = query.filter(Bidang.id.in_(list_ids))
        query = query.distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()

notaris = CRUDNotaris(Notaris)