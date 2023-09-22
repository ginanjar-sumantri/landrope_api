from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.kjb_model import KjbHd, KjbBebanBiaya, KjbHarga, KjbTermin, KjbRekening, KjbPenjual, KjbDt
from schemas.beban_biaya_sch import BebanBiayaCreateSch
from schemas.kjb_hd_sch import KjbHdCreateSch, KjbHdUpdateSch, KjbHdForTerminByIdSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc
import crud
import json

class CRUDKjbHd(CRUDBase[KjbHd, KjbHdCreateSch, KjbHdUpdateSch]):
    async def create_kjb_hd(self, *, obj_in: KjbHdCreateSch | KjbHd, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> KjbHd :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id

        
        for dt in obj_in.details:
            alashak = await crud.kjb_dt.get_by_alashak(alashak=dt.alashak)
            if alashak:
                raise HTTPException(status_code=409, detail=f"alashak {dt.alashak} ada di KJB lain ({alashak.kjb_code})")
            
            detail = KjbDt(jenis_alashak=dt.jenis_alashak,
                           alashak=dt.alashak,
                           posisi_bidang=dt.posisi_bidang,
                           harga_akta=dt.harga_akta,
                           harga_transaksi=dt.harga_transaksi,
                           luas_surat=dt.luas_surat,
                           desa_id=dt.desa_id,
                           project_id=dt.project_id,
                           pemilik_id=dt.pemilik_id,
                           jenis_surat_id=dt.jenis_surat_id,
                           created_by_id=created_by_id,
                           updated_by_id=created_by_id)
            
            db_obj.kjb_dts.append(detail)

        
        for i in obj_in.rekenings:
            rekening = KjbRekening(nama_pemilik_rekening=i.nama_pemilik_rekening,
                                    bank_rekening=i.bank_rekening,
                                    nomor_rekening=i.nomor_rekening,
                                    created_by_id=created_by_id,
                                    updated_by_id=created_by_id)
            
            db_obj.rekenings.append(rekening)
        
        for j in obj_in.hargas:
            obj_harga = next((harga for harga in db_obj.hargas if harga.jenis_alashak == j.jenis_alashak), None)
            if obj_harga:
                raise HTTPException(status_code=409, detail=f"Harga {j.jenis_alashak} double input")
            
            termins = []
            for l in j.termins:
                termin = KjbTermin(jenis_bayar=l.jenis_bayar,
                                        nilai=l.nilai,
                                        created_by_id=created_by_id,
                                        updated_by_id=created_by_id)
                termins.append(termin)
            
            harga = KjbHarga(jenis_alashak=j.jenis_alashak,
                                harga_akta=j.harga_akta,
                                harga_transaksi=j.harga_transaksi,
                                created_by_id=created_by_id,
                                updated_by_id=created_by_id)
            
            if len(termins) > 0:
                harga.termins = termins
            
            db_obj.hargas.append(harga)
        
        for k in obj_in.bebanbiayas:
            if k.beban_biaya_id != "":
                obj_bebanbiaya = await crud.bebanbiaya.get(id=UUID(k.beban_biaya_id))
            else:
                obj_bebanbiaya = await crud.bebanbiaya.get_by_name(name=k.beban_biaya_name)
                
            if obj_bebanbiaya is None:
                    obj_bebanbiaya_in = BebanBiayaCreateSch(name=k.beban_biaya_name, is_active=True)
                    obj_bebanbiaya = await crud.bebanbiaya.create(obj_in=obj_bebanbiaya_in)
                
            bebanbiaya = KjbBebanBiaya(beban_biaya_id=obj_bebanbiaya.id,
                                            beban_pembeli=k.beban_pembeli,
                                            created_by_id=created_by_id,
                                            updated_by_id=created_by_id)
            db_obj.bebanbiayas.append(bebanbiaya)
        
        for p in obj_in.penjuals:
            penjual = KjbPenjual(pemilik_id=p.pemilik_id, created_by_id=created_by_id,
                                    updated_by_id=created_by_id)
            db_obj.penjuals.append(penjual)

        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj
    
    async def get_multi_kjb_not_draft(
        self,
        *,
        keyword:str | None = None,
        filter_query: str | None = None,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: KjbHd | Select[KjbHd] | None = None,
        db_session: AsyncSession | None = None,
        join:bool | None = False
    ) -> Page[KjbHd]:
        db_session = db_session or db.session

        columns = self.model.__table__.columns

        find = False
        for c in columns:
            if c.name == order_by:
                find = True
                break
        
        if order_by is None or find == False:
            order_by = "id"
        
        if query is None:
            query = select(self.model)

        if filter_query is not None and filter_query:
            filter_query = json.loads(filter_query)
            
            for key, value in filter_query.items():
                query = query.where(getattr(self.model, key) == value)
        
        filter_clause = None

        if keyword:
            for attr in columns:
                if not "CHAR" in str(attr.type) or attr.name.endswith("_id") or attr.name == "id":
                    continue

                condition = getattr(self.model, attr.name).ilike(f'%{keyword}%')
                if filter_clause is None:
                    filter_clause = condition
                else:
                    filter_clause = or_(filter_clause, condition)
                
        #Filter Column yang berelasi dengan object (untuk case tertentu)
        if join:
            relationships = self.model.__mapper__.relationships

            for r in relationships:
                if r.uselist: #filter object list dilewati
                    continue
                if class_relation.__name__.lower() == "worker":
                    continue

                class_relation = r.mapper.class_
                query = query.join(class_relation)

                if keyword:
                    relation_columns = class_relation.__table__.columns
                            
                    for c in relation_columns:
                        if not "CHAR" in str(c.type) or c.name.endswith("_id") or c.name == "id":
                            continue
                        if "updated" in c.name or "created" in c.name:
                            continue
                        
                        cond = getattr(class_relation, c.name).ilike(f'%{keyword}%')
                        if filter_clause is None:
                            filter_clause = cond
                        else:
                            filter_clause = or_(filter_clause, cond)

        if filter_clause is not None:        
            query = query.filter(filter_clause)

        if order == OrderEnumSch.ascendent:
            query = query.order_by(columns[order_by].asc())
        else:
            query = query.order_by(columns[order_by].desc())

        query.where(self.model.is_draft != True)
            
        return await paginate(db_session, query, params)
    
    async def get_by_id_for_termin(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> KjbHdForTerminByIdSch | None:
        db_session = db_session or db.session
        query = select(KjbHd.id,
                       KjbHd.code,
                       KjbHd.nama_group,
                       KjbHd.utj_amount,
                       ).select_from(KjbHd
                            ).where(KjbHd.id == id)

        response = await db_session.execute(query)

        return response.fetchone()

kjb_hd = CRUDKjbHd(KjbHd)

