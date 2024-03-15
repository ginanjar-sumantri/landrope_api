from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, delete, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.kjb_model import KjbDt, KjbHd
from models.desa_model import Desa
from models.pemilik_model import Pemilik
from models.bidang_model import Bidang
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from models.planing_model import Planing
from models.desa_model import Desa
from schemas.request_peta_lokasi_sch import (RequestPetaLokasiCreateSch, RequestPetaLokasiHdSch, 
                                            RequestPetaLokasiForInputHasilSch, RequestPetaLokasiUpdateSch, RequestPetaLokasiSch, RequestPetaLokasiUpdateExtSch)
from typing import List, Dict, Any
from common.ordered import OrderEnumSch
from uuid import UUID
from datetime import datetime

class CRUDRequestPetaLokasi(CRUDBase[RequestPetaLokasi, RequestPetaLokasiCreateSch, RequestPetaLokasiUpdateSch]):
    async def updates_(self, 
                     *,
                     code:str|None,
                     obj_currents : list[RequestPetaLokasi], 
                     obj_new :  RequestPetaLokasiUpdateExtSch| Dict[str, Any] | RequestPetaLokasi,
                     updated_by_id: UUID | str | None = None,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> KjbHd :
        
        db_session = db.session

        #delete all data detail current when not exists in schema update
        await db_session.execute(delete(RequestPetaLokasi).where(and_(RequestPetaLokasi.id.notin_(r.id for r in obj_new.datas if r.id is not None), 
                                                        RequestPetaLokasi.code == code)))
        

        for req in obj_new.datas:
            existing_req = next((r for r in obj_currents if r.id == req.id), None)
            if existing_req:
                request_petlok = req.dict(exclude_unset=True)
                for key, value in request_petlok.items():
                    setattr(existing_req, key, value)
                existing_req.updated_at = datetime.utcnow()
                existing_req.updated_by_id = updated_by_id
                existing_req.tanggal_terima_berkas = obj_new.tanggal_terima_berkas
                existing_req.keterangan_req_petlok_id = req.keterangan_req_petlok_id
                existing_req.luas_ukur = req.luas_ukur
                db_session.add(existing_req)
            else:
                new_request_petlok = RequestPetaLokasi(**req.dict(exclude={"tanggal_terima_berkas", "code"}), 
                                                    tanggal_terima_berkas=obj_new.tanggal_terima_berkas, 
                                                    code=obj_new.code, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                db_session.add(new_request_petlok)
            
        if with_commit:
            await db_session.commit()

        return existing_req
    
    async def get_by_id(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> RequestPetaLokasi | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.id == id
                                        ).options(selectinload(RequestPetaLokasi.kjb_dt
                                                            ).options(selectinload(KjbDt.kjb_hd))
                                        ).options(selectinload(RequestPetaLokasi.hasil_peta_lokasi)
                                        ).options(selectinload(RequestPetaLokasi.keterangan_req_petlok)
                                                )
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_header_paginated(self, *, params: Params | None = Params(),
                                  order: OrderEnumSch | None = OrderEnumSch.descendent,
                                  keyword:str | None = None,
                                  db_session: AsyncSession | None = None) -> Page[RequestPetaLokasiHdSch]:
        db_session = db_session or db.session

        columns = RequestPetaLokasi.__table__.columns

        query = select(
            RequestPetaLokasi.code,
            Desa.name.label("desa_name"),
            KjbHd.mediator,
            KjbHd.nama_group.label("group"),
            KjbHd.code.label("kjb_hd_code")
        ).select_from(RequestPetaLokasi
                    ).outerjoin(KjbDt, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                    ).outerjoin(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                    ).outerjoin(Desa, Desa.id == KjbHd.desa_id).distinct()

        filter_clause = None

        if keyword:
            query = query.filter(
                or_(
                    RequestPetaLokasi.code.ilike(f'%{keyword}%'),
                    KjbDt.alashak.ilike(f'%{keyword}%'),
                    KjbHd.code.ilike(f'%{keyword}%'),
                    KjbHd.mediator.ilike(f'%{keyword}%'),
                    KjbHd.nama_group.ilike(f'%{keyword}%'),
                    Desa.name.ilike(f'%{keyword}%'),
                )
            )
            
        if filter_clause is not None:        
            query = query.filter(filter_clause)
        
        if order == OrderEnumSch.ascendent:
            query = query.order_by(columns["code"].asc())
        else:
            query = query.order_by(columns["code"].desc())
        
        query = query.distinct()

        return await paginate(db_session, query, params)
    
    async def get_multi_header_has_input_petlok_paginated(self, *, params: Params | None = Params(),
                                  order: OrderEnumSch | None = OrderEnumSch.descendent,
                                  keyword:str | None = None,
                                  db_session: AsyncSession | None = None) -> Page[RequestPetaLokasiHdSch]:
        db_session = db_session or db.session

        columns = RequestPetaLokasi.__table__.columns

        query = select(
            RequestPetaLokasi.code,
            Desa.name.label("desa_name"),
            KjbHd.mediator,
            KjbHd.nama_group.label("group"),
            KjbHd.code.label("kjb_hd_code")
                    ).outerjoin(KjbDt, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                    ).outerjoin(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                    ).outerjoin(Desa, Desa.id == KjbHd.desa_id
                    ).where(RequestPetaLokasi.hasil_peta_lokasi != None).distinct()

        filter_clause = None

        if keyword:
            query = query.filter(
                or_(
                    RequestPetaLokasi.code.ilike(f'%{keyword}%'),
                    KjbDt.alashak.ilike(f'%{keyword}%'),
                    KjbHd.code.ilike(f'%{keyword}%'),
                    KjbHd.mediator.ilike(f'%{keyword}%'),
                    KjbHd.nama_group.ilike(f'%{keyword}%'),
                    Desa.name.ilike(f'%{keyword}%'),
                )
            )
            
        if filter_clause is not None:        
            query = query.filter(filter_clause)
        
        if order == OrderEnumSch.ascendent:
            query = query.order_by(columns["code"].asc())
        else:
            query = query.order_by(columns["code"].desc())
        
        query = query.distinct()

        return await paginate(db_session, query, params)
    
    async def get_multi_detail_paginated(self, *, params: Params | None = Params(),
                                  order: OrderEnumSch | None = OrderEnumSch.descendent,
                                  keyword:str | None,
                                  filter_list:str|None = None,
                                  db_session: AsyncSession | None = None) -> Page[RequestPetaLokasiForInputHasilSch]:
        db_session = db_session or db.session

        columns = RequestPetaLokasi.__table__.columns

        # subquery = select(Address.user_id).subquery()
        # query = select(User).add_columns(User.id, User.name, subquery.exists().label("has_address"))
        
        query = select(
            RequestPetaLokasi.id,
            RequestPetaLokasi.code,
            KjbDt.alashak,
            Pemilik.name.label("pemilik_name"),
            KjbHd.code.label("kjb_hd_code"),
            KjbHd.mediator,
            KjbDt.id.label("kjb_dt_id"),
            Bidang.id_bidang,
            Bidang.id.label("bidang_id"),
            HasilPetaLokasi.file_path,
            HasilPetaLokasi.id.label("hasil_peta_lokasi_id"),
            HasilPetaLokasi.hasil_analisa_peta_lokasi,
            HasilPetaLokasi.status_hasil_peta_lokasi,
            HasilPetaLokasi.remark,
            Desa.name.label("desa_name")
        ).select_from(RequestPetaLokasi
                    ).outerjoin(KjbDt, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                    ).outerjoin(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                    ).outerjoin(Pemilik, Pemilik.id == KjbDt.pemilik_id
                    ).outerjoin(HasilPetaLokasi, HasilPetaLokasi.kjb_dt_id == KjbDt.id
                    ).outerjoin(Bidang, Bidang.id == HasilPetaLokasi.bidang_id
                    ).outerjoin(Planing, Planing.id == HasilPetaLokasi.planing_id
                    ).outerjoin(Desa, Desa.id == Planing.desa_id)

        filter_clause = None

        if keyword:
            query = query.filter(
                or_(
                    RequestPetaLokasi.code.ilike(f'%{keyword}%'),
                    KjbDt.alashak.ilike(f'%{keyword}%'),
                    KjbHd.code.ilike(f'%{keyword}%'),
                    KjbHd.mediator.ilike(f'%{keyword}%'),
                    Pemilik.name.ilike(f'%{keyword}%'),
                    Bidang.id_bidang.ilike(f'%{keyword}%')
                )
            )

        if filter_list == 'outstanding':
            query = query.filter(KjbDt.hasil_peta_lokasi == None)
        
        if filter_list == 'outstandinggupbt':
            list_id = await self.get_outstanding_gu_pbt()
            ids = [id["id"] for id in list_id]

            query = query.filter(HasilPetaLokasi.id.in_(ids))
            
        if filter_clause is not None:        
            query = query.filter(filter_clause)
        
        if order == OrderEnumSch.ascendent:
            query = query.order_by(columns["updated_at"].asc())
        else:
            query = query.order_by(columns["updated_at"].desc())
        
        
        return await paginate(db_session, query, params)
    
    async def get_multi_detail_has_input_petlok_paginated(self, *, params: Params | None = Params(),
                                  order: OrderEnumSch | None = OrderEnumSch.descendent,
                                  code:str | None = None,
                                  db_session: AsyncSession | None = None) -> Page[RequestPetaLokasiForInputHasilSch]:
        db_session = db_session or db.session

        columns = RequestPetaLokasi.__table__.columns

        # subquery = select(Address.user_id).subquery()
        # query = select(User).add_columns(User.id, User.name, subquery.exists().label("has_address"))
        
        query = select(
            RequestPetaLokasi.id,
            RequestPetaLokasi.code,
            KjbDt.alashak,
            Pemilik.name.label("pemilik_name"),
            KjbHd.code.label("kjb_hd_code"),
            KjbHd.mediator,
            KjbDt.id.label("kjb_dt_id"),
            Bidang.id_bidang,
            Bidang.id.label("bidang_id"),
            HasilPetaLokasi.file_path,
            HasilPetaLokasi.id.label("hasil_peta_lokasi_id"),
            HasilPetaLokasi.hasil_analisa_peta_lokasi,
            HasilPetaLokasi.status_hasil_peta_lokasi,
            HasilPetaLokasi.remark,
            Desa.name.label("desa_name")).outerjoin(KjbDt, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                    ).outerjoin(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                    ).outerjoin(Pemilik, Pemilik.id == KjbDt.pemilik_id
                    ).join(HasilPetaLokasi, HasilPetaLokasi.kjb_dt_id == KjbDt.id
                    ).outerjoin(Bidang, Bidang.id == HasilPetaLokasi.bidang_id
                    ).outerjoin(Planing, Planing.id == HasilPetaLokasi.planing_id
                    ).outerjoin(Desa, Desa.id == Planing.desa_id
                    ).where(RequestPetaLokasi.code == code)

        filter_clause = None

        if order == OrderEnumSch.ascendent:
            query = query.order_by(columns["updated_at"].asc())
        else:
            query = query.order_by(columns["updated_at"].desc())
        
        
        return await paginate(db_session, query, params)
    
    async def get_all_by_code(self, *, code: str, db_session : AsyncSession | None = None) -> List[RequestPetaLokasi] | None:
        db_session = db_session or db.session

        query = select(self.model).where(self.model.code == code
                                            ).options(selectinload(RequestPetaLokasi.kjb_dt
                                                                    ).options(selectinload(KjbDt.kjb_hd)
                                                                    ).options(selectinload(KjbDt.pemilik
                                                                                            ).options(selectinload(Pemilik.kontaks))
                                                                    ).options(selectinload(KjbDt.desa_by_ttn)
                                                                    ).options(selectinload(KjbDt.project_by_ttn)
                                                                    ).options(selectinload(KjbDt.kjb_hd
                                                                                            ).options(selectinload(KjbHd.desa))
                                                                    )
                                            ).options(selectinload(RequestPetaLokasi.hasil_peta_lokasi
                                                                    ).options(selectinload(HasilPetaLokasi.bidang))
                                            )

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_all_by_code_have_input_petlok(self, *, code: str, db_session : AsyncSession | None = None) -> List[RequestPetaLokasi] | None:
        db_session = db_session or db.session

        query = select(self.model).where(and_(self.model.code == code, self.model.hasil_peta_lokasi != None))
        query = query.options(selectinload(RequestPetaLokasi.kjb_dt
                                                                    ).options(selectinload(KjbDt.kjb_hd)
                                                                    ).options(selectinload(KjbDt.pemilik
                                                                                            ).options(selectinload(Pemilik.kontaks))
                                                                    ).options(selectinload(KjbDt.desa_by_ttn)
                                                                    ).options(selectinload(KjbDt.project_by_ttn)
                                                                    ).options(selectinload(KjbDt.kjb_hd
                                                                                            ).options(selectinload(KjbHd.desa))
                                                                    )
                                            ).options(selectinload(RequestPetaLokasi.hasil_peta_lokasi
                                                                    ).options(selectinload(HasilPetaLokasi.bidang))
                                            )

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_by_kjb_dt_id(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> RequestPetaLokasi | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.kjb_dt_id == id)
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def remove_kjb_dt(self, *, id:UUID | str, db_session : AsyncSession | None = None) -> RequestPetaLokasi:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.kjb_dt_id == id)
        response = await db_session.execute(query)

        obj = response.scalar_one()
        await db_session.delete(obj)
        await db_session.commit()
        return obj

    async def get_outstanding_gu_pbt(self, *, db_session : AsyncSession | None = None) -> list[UUID]:
        db_session = db_session or db.session
        query = text(f"""
                    with subquery_hasil_petlok as (
                    select 
                        hpl.id,
                        dk.name,
                        dt.meta_data
                    from 
                        hasil_peta_lokasi hpl
                    INNER JOIN 
                        bidang b ON b.id = hpl.bidang_id
                    INNER JOIN 
                        bundle_hd hd ON hd.id = b.bundle_hd_id
                    INNER JOIN
                        bundle_dt dt ON hd.id = dt.bundle_hd_id
                    INNER JOIN
                        dokumen dk ON dk.id = dt.dokumen_id 
                        and dk.name IN ('GAMBAR UKUR PBT', 'GAMBAR UKUR PERORANGAN', 'PBT PERORANGAN', 'PBT PT')
                    )
                    SELECT 
                        hpl.id
                    FROM hasil_peta_lokasi hpl
                    LEFT OUTER JOIN 
                        subquery_hasil_petlok gu_pt ON gu_pt.id = hpl.id AND gu_pt.name = 'GAMBAR UKUR PBT'
                    LEFT OUTER JOIN 
                        subquery_hasil_petlok gu_perorangan ON gu_perorangan.id = hpl.id AND gu_perorangan.name = 'GAMBAR UKUR PERORANGAN'
                    LEFT OUTER JOIN 
                        subquery_hasil_petlok pbt_pt ON pbt_pt.id = hpl.id AND pbt_pt.name = 'PBT PT'
                    LEFT OUTER JOIN 
                        subquery_hasil_petlok pbt_perorangan ON pbt_perorangan.id = hpl.id AND pbt_perorangan.name = 'PBT PERORANGAN'
                    WHERE
                        (gu_pt.meta_data IS NOT NULL AND hpl.luas_gu_pt = 0)
                        OR (gu_perorangan.meta_data IS NOT NULL AND hpl.luas_gu_perorangan = 0)
                        OR (pbt_pt.meta_data IS NOT NULL AND hpl.luas_pbt_pt = 0)
                        OR (pbt_perorangan.meta_data IS NOT NULL AND hpl.luas_pbt_perorangan = 0)
                    """)

        response = await db_session.execute(query)

        return response.fetchall()
    
request_peta_lokasi = CRUDRequestPetaLokasi(RequestPetaLokasi)