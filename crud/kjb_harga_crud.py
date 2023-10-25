from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from common.enum import JenisAlashakEnum
from crud.base_crud import CRUDBase
from models import KjbHarga, KjbTermin, Spk, Invoice, Termin
from schemas.kjb_harga_sch import KjbHargaCreateSch, KjbHargaUpdateSch, KjbHargaCreateExtSch, KjbHargaForCloud, KjbHargaAktaSch
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
    
    async def get_by_kjb_hd_id_and_jenis_alashak(self, *, 
                  kjb_hd_id: UUID | str, 
                  jenis_alashak:JenisAlashakEnum,
                  db_session: AsyncSession | None = None) -> KjbHarga | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.kjb_hd_id == kjb_hd_id, self.model.jenis_alashak == jenis_alashak)
                                        ).options(selectinload(KjbHarga.termins)
                                        )
        response = await db_session.execute(query)

        return response.scalars().one_or_none()
    
    async def get_harga_by_id_for_cloud(self, *, 
                  kjb_hd_id: UUID | str, 
                  jenis_alashak:JenisAlashakEnum,
                  db_session: AsyncSession | None = None) -> KjbHargaForCloud | None:
        
        db_session = db_session or db.session
        query = select(self.model.harga_akta, self.model.harga_transaksi, self.model.id).where(and_(self.model.kjb_hd_id == kjb_hd_id, self.model.jenis_alashak == jenis_alashak))
        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_harga_akta_by_termin_id_for_printout(self, *, 
                  termin_id: UUID | str,
                  db_session: AsyncSession | None = None) -> list[KjbHargaAktaSch] | None:
        
        db_session = db_session or db.session
        query = select(KjbHarga.harga_akta).join(KjbTermin, KjbTermin.kjb_harga_id == KjbHarga.id
                                ).join(Spk, Spk.kjb_termin_id == KjbTermin.id
                                ).join(Invoice, Invoice.spk_id == Spk.id
                                ).join(Termin, Termin.id == Invoice.termin_id
                                ).where(Termin.id == termin_id).distinct()
        
        response = await db_session.execute(query)

        return response.fetchall()

kjb_harga = CRUDKjbHarga(KjbHarga)