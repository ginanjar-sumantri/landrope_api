from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, func, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from common.enum import StatusPetaLokasiEnum
from crud.base_crud import CRUDBase
from models import KjbHd, KjbDt, RequestPetaLokasi, Pemilik, HasilPetaLokasi, Planing, BundleHd, BundleDt, Workflow
from models.master_model import HargaStandard
from schemas.kjb_dt_sch import KjbDtCreateSch, KjbDtUpdateSch, KjbDtSrcForGUSch, KjbDtForCloud, KjbDtListSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDKjbDt(CRUDBase[KjbDt, KjbDtCreateSch, KjbDtUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> KjbDt | None:
        
        db_session = db_session or db.session
        
        query = select(KjbDt).where(KjbDt.id == id).options(selectinload(KjbDt.pemilik
                                                                        ).options(selectinload(Pemilik.kontaks))
                                                ).options(selectinload(KjbDt.kjb_hd)
                                                ).options(selectinload(KjbDt.jenis_surat)
                                                ).options(selectinload(KjbDt.bundlehd
                                                                        ).options(selectinload(BundleHd.bundledts
                                                                                            ).options(selectinload(BundleDt.dokumen))
                                                                        )
                                                ).options(selectinload(KjbDt.tanda_terima_notaris_hd)
                                                ).options(selectinload(KjbDt.request_peta_lokasi)
                                                ).options(selectinload(KjbDt.hasil_peta_lokasi
                                                                        ).options(selectinload(HasilPetaLokasi.bidang)))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_paginated_ordered(self, *, params: Params | None = Params(),
                                  order: OrderEnumSch | None = OrderEnumSch.descendent,
                                  keyword:str | None = None,
                                  filter:str | None = None,
                                  db_session: AsyncSession | None = None) -> Page[KjbDtListSch]:
        db_session = db_session or db.session

        query = select(func.distinct(KjbDt.id),
                   KjbDt.id, 
                   KjbDt.alashak,
                   KjbDt.jenis_alashak,
                   KjbDt.harga_akta,
                   KjbDt.harga_transaksi,
                   KjbDt.status_peta_lokasi,
                   KjbDt.luas_surat,
                   KjbDt.luas_surat_by_ttn,
                   KjbDt.created_at,
                   KjbHd.code.label("kjb_code"),
                   KjbDt.kjb_hd_id,
                   Workflow.last_status.label("status_workflow"),
                   Workflow.step_name.label("step_name_workflow"),
                   func.coalesce(func.max(HargaStandard.harga), 0).label("harga_standard")
                    ).join(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                    ).outerjoin(Planing, Planing.desa_id == KjbDt.desa_by_ttn_id
                    ).outerjoin(HargaStandard, HargaStandard.planing_id == Planing.id
                    ).outerjoin(Workflow, Workflow.reference_id == KjbHd.id)
        
        if filter == "lebihdari":
            query = query.filter(KjbDt.harga_transaksi > HargaStandard.harga)
        
        if filter == "kurangdarisamadengan":
            query = query.filter(KjbDt.harga_transaksi <= HargaStandard.harga)
        
        if filter == "requestpetlok":
            query = query.filter(or_(KjbHd.is_draft != True, KjbHd.is_draft is None))

        if keyword:
            query = query.filter(
                or_(
                    KjbDt.alashak.ilike(f'%{keyword}%'),
                    KjbHd.code.ilike(f'%{keyword}%'),
                    KjbDt.jenis_alashak.ilike(f'%{keyword}%')
                )
            )
        
        
        query = query.group_by(KjbDt.id, KjbHd.code, Workflow.last_status, Workflow.step_name
                    ).order_by(KjbDt.id, KjbHd.code, KjbDt.created_at.desc())

        return await paginate(db_session, query, params)
    
    async def get_multi_by_kjb_hd_id(self, 
                                    *,
                                    kjb_hd_id:UUID,
                                  db_session: AsyncSession | None = None) -> list[KjbDt]:
        db_session = db_session or db.session

        query = select(KjbDt
                    ).join(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                    ).where(KjbDt.kjb_hd_id == kjb_hd_id
                    ).options(selectinload(KjbDt.hasil_peta_lokasi
                                    ).options(selectinload(HasilPetaLokasi.bidang))
                    )

        response = await db_session.execute(query)
        return response.scalars().all()


    async def get_multi_for_petlok(self, *,
                                    params: Params | None = Params(),
                                    kjb_hd_id:UUID | None,
                                    no_order:str | None,
                                    db_session : AsyncSession | None = None) -> List[KjbDt] | None:
        db_session = db_session or db.session

        if no_order is None:
            no_order = ""

        query = select(self.model
                       ).select_from(self.model
                                     ).outerjoin(RequestPetaLokasi, self.model.id == RequestPetaLokasi.kjb_dt_id
                                     ).where(and_(
                                                    self.model.kjb_hd_id == kjb_hd_id,
                                                    self.model.status_peta_lokasi == StatusPetaLokasiEnum.Lanjut_Peta_Lokasi,
                                                    or_(
                                                        RequestPetaLokasi.code == no_order,
                                                        self.model.request_peta_lokasi == None
                                                    )
                                                )
                                            )
        
        
        return await paginate(db_session, query, params)
    
    async def get_multi_for_tanda_terima_notaris(
                        self, *, 
                        params: Params | None = Params(),
                        db_session: AsyncSession | None = None) -> Page[KjbDt]:
        
        db_session = db_session or db.session

        query = select(self.model
                       ).select_from(self.model
                                     ).outerjoin(RequestPetaLokasi, self.model.id == RequestPetaLokasi.kjb_dt_id
                                                 ).where(self.model.request_peta_lokasi == None)

        return await paginate(db_session, query, params)

    async def get_by_alashak(self, *, alashak:str, db_session: AsyncSession | None = None) -> KjbDt | None:
        db_session = db_session or db.session
        query = select(self.model).where(func.lower(func.trim(func.replace(self.model.alashak, ' ', ''))) == alashak.strip().lower().replace(' ', '')
                                         ).options(selectinload(KjbDt.kjb_hd))
        response = await db_session.execute(query)

        return response.scalars().first()
    
    async def get_by_alashak_and_kjb_hd_id(self, *, alashak:str | None, kjb_hd_id:UUID | None, db_session: AsyncSession | None = None) -> KjbDt | None:
        db_session = db_session or db.session
        query = select(self.model
                       ).where(and_(self.model.kjb_hd_id != kjb_hd_id, func.lower(func.trim(func.replace(self.model.alashak, ' ', ''))) == alashak.strip().lower().replace(' ', ''))
                               ).options(selectinload(KjbDt.kjb_hd))
        response = await db_session.execute(query)

        return response.scalars().first()
    
    async def get_multi_for_order_gu(self, *, skip : int = 0, limit : int = 100, query : KjbDt | Select[KjbDt] | None = None, db_session : AsyncSession | None = None
                        ) -> List[KjbDtSrcForGUSch]:
        db_session = db_session or db.session
        if query is None:
            query = select(self.model).offset(skip).limit(limit).order_by(self.model.id)

        response =  await db_session.execute(query)
        return response.fetchall()
    
    async def get_by_id_for_cloud(
                    self, 
                    *, 
                    id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> KjbDtForCloud | None:
        
        db_session = db_session or db.session
        query = text(f"""
                    select
                    id,
                    "group",
                    kjb_hd_id,
                    jenis_alashak,
                    jenis_surat_id,
                    alashak,
                    harga_akta,
                    harga_transaksi,
                    harga_ptsl,
                    bundle_hd_id
                    from kjb_dt
                    where id = '{str(id)}'
                    """)

        response = await db_session.execute(query)

        return response.fetchone()
    
kjb_dt = CRUDKjbDt(KjbDt)