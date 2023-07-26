from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import exc
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.desa_model import Desa
from models.code_counter_model import CodeCounterEnum
from schemas.desa_sch import DesaCreateSch, DesaUpdateSch, DesaSch
from common.generator import generate_code
from typing import List
from uuid import UUID

from datetime import datetime

class CRUDDesa(CRUDBase[Desa, DesaCreateSch, DesaUpdateSch]):
    async def create(self, *, 
                     obj_in: DesaCreateSch | Desa, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> Desa :
        db_session = db_session or db.session
        db_obj = Desa.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
        
        db_obj.code = await generate_code(CodeCounterEnum.Desa, db_session=db_session, with_commit=False)
        
        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
       
        await db_session.refresh(db_obj)
        return db_obj

    
desa = CRUDDesa(Desa)