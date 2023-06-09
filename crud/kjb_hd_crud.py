from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.kjb_model import KjbHd, KjbBebanBiaya, KjbCaraBayar, KjbRekening
from models.master_model import BebanBiaya
from schemas.kjb_hd_sch import KjbHdCreateSch, KjbHdUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc
import crud

class CRUDKjbHd(CRUDBase[KjbHd, KjbHdCreateSch, KjbHdUpdateSch]):
    async def create_kjb_hd(self, *, obj_in: KjbHdCreateSch | KjbHd, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> KjbHd :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id

        try:
            
            for i in obj_in.rekenings:
                rekening = KjbRekening(nama_pemilik_rekening=i.nama_pemilik_rekening,
                                        bank_rekening=i.bank_rekening,
                                        nomor_rekening=i.nomor_rekening)
                
                db_obj.rekenings.append(rekening)
            
            for j in obj_in.carabayars:
                carabayar = KjbCaraBayar(jenis_bayar=j.jenis_bayar,
                                         nilai=j.nilai)
                
                db_obj.carabayars.append(carabayar)
            
            for k in obj_in.bebanbiayas:
                obj_bebanbiaya = await crud.bebanbiaya.get(id=k.beban_biaya_id)

                if obj_bebanbiaya is None:
                    obj_bebanbiaya_in = BebanBiaya(name=k.beban_biaya_name)
                    obj_bebanbiaya = await crud.bebanbiaya.create(obj_in=obj_bebanbiaya_in)


                bebanbiaya = KjbBebanBiaya(beban_biaya_id=obj_bebanbiaya.id,
                                               beban_pembeli=k.beban_pembeli)
                db_obj.bebanbiayas.append(bebanbiaya)

            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj

kjb_hd = CRUDKjbHd(KjbHd)

