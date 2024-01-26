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
from models import Pemilik, Kontak, Rekening, Bidang
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
    async def get_by_pemilik_id(self, *, pemilik_id: UUID | str | None = None, db_session: AsyncSession | None = None) -> List[Rekening] | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.pemilik_id == pemilik_id)
        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_by_rekening_bank_pemilik(self, *, nama_pemilik_rekening: str, 
                                           nomor_rekening:str,
                                           bank_rekening:str, 
                                           db_session: AsyncSession | None = None) -> Rekening | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.nama_pemilik_rekening.strip().lower() == nama_pemilik_rekening.strip().lower(),
                                         self.model.nomor_rekening.strip() == nomor_rekening.strip(),
                                         self.model.bank_rekening.strip().lower() == bank_rekening.strip().lower())
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    
    async def get_multi_by_bidang_ids(self, 
                        list_ids: List[UUID | str], 
                        db_session : AsyncSession | None = None
                        ) -> List[Rekening]:
        
        db_session = db_session or db.session

        query = select(Rekening)
        query = query.join(Pemilik, Pemilik.id == Rekening.pemilik_id)
        query = query.join(Bidang, Bidang.pemilik_id == Pemilik.id)
        query = query.filter(Bidang.id.in_(list_ids))
        query = query.distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()

rekening = CRUDRekening(Rekening)

