from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.kjb_model import KjbRekening
from schemas.kjb_rekening_sch import KjbRekeningCreateSch, KjbRekeningUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDKjbRekening(CRUDBase[KjbRekening, KjbRekeningCreateSch, KjbRekeningUpdateSch]):
    async def delete_multiple_where_not_in(
            self, 
            *, 
            ids:list[UUID] = None,
            kjb_hd_id:UUID,
            db_session : AsyncSession | None = None,
            with_commit:bool | None = True
            ) -> bool:
        
        db_session = db_session or db.session
        
        query = self.model.__table__.delete().where(and_(self.model.id.notin_(ids), self.model.kjb_hd_id == kjb_hd_id))

        try:
            await db_session.execute(query)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=422, detail="failed delete data")

        return True

kjb_rekening = CRUDKjbRekening(KjbRekening)