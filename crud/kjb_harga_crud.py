from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.kjb_model import KjbHarga, KjbTermin
from schemas.kjb_harga_sch import KjbHargaCreateSch, KjbHargaUpdateSch, KjbHargaCreateExtSch
from schemas.kjb_termin_sch import KjbTerminSch, KjbTerminCreateExtSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc
import crud

class CRUDKjbHarga(CRUDBase[KjbHarga, KjbHargaCreateSch, KjbHargaUpdateSch]):
    async def create(self, *, obj_in: KjbHargaCreateSch | KjbHarga | KjbHargaCreateExtSch, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> KjbHarga :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
        try:

            for i in obj_in.termins:
                termin = KjbTermin(jenis_bayar=i.jenis_bayar, nilai=i.nilai)
                db_obj.termins.append(termin)

            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj

kjb_harga = CRUDKjbHarga(KjbHarga)