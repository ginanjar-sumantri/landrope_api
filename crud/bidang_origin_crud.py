from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from crud.base_crud import CRUDBase
from models import BidangOrigin
from schemas.bidang_origin_sch import BidangOriginSch
from typing import List
from uuid import UUID

class CRUDBidangOrigin(CRUDBase[BidangOrigin, BidangOriginSch, BidangOriginSch]):
    async def create_(self, *, 
                     obj_in: BidangOriginSch | BidangOrigin,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> BidangOrigin :
        
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        
        try:
            db_session.add(db_obj)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)
        return db_obj

bidang_origin = CRUDBidangOrigin(BidangOrigin)