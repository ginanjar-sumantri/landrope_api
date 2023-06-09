from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.pemilik_model import Pemilik, Kontak, Rekening
from schemas.pemilik_sch import PemilikCreateSch, PemilikUpdateSch
from schemas.kontak_sch import KontakCreateSch, KontakUpdateSch
from schemas.rekening_sch import RekeningCreateSch, RekeningUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime

class CRUDPemilik(CRUDBase[Pemilik, PemilikCreateSch, PemilikUpdateSch]):
    async def create_pemilik(self, *, obj_in: PemilikCreateSch | Pemilik, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> Pemilik :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id

        try:
            
            for i in obj_in.kontaks:
                kontak = Kontak(nomor_telepon=i.nomor_telepon)
                db_obj.kontaks.append(kontak)

            
            for i in obj_in.rekenings:
                rekening = Rekening(nama_pemilik_rekening=i.nama_pemilik_rekening,
                                    bank_rekening=i.bank_rekening,
                                    nomor_rekening=i.nomor_rekening)
                db_obj.rekenings.append(rekening)


            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj

pemilik = CRUDPemilik(Pemilik)


class CRUDKontak(CRUDBase[Kontak, KontakCreateSch, KontakUpdateSch]):
    async def get_by_pemilik_id(self, *, pemilik_id: UUID | str, db_session: AsyncSession | None = None) -> List[Kontak] | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.pemilik_id == pemilik_id)
        response = await db_session.execute(query)

        return response.scalars().all()

kontak = CRUDKontak(Kontak)

class CRUDRekening(CRUDBase[Rekening, RekeningCreateSch, RekeningUpdateSch]):
    pass

rekening = CRUDRekening(Rekening)

