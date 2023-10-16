from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import HasilPetaLokasi, HasilPetaLokasiDetail, Planing, Skpt
from schemas.hasil_peta_lokasi_sch import HasilPetaLokasiCreateSch, HasilPetaLokasiUpdateSch, HasilPetaLokasiCreateExtSch, HasilPetaLokasiUpdateCloud
from typing import List
from uuid import UUID
from datetime import datetime

class CRUDHasilPetaLokasi(CRUDBase[HasilPetaLokasi, HasilPetaLokasiCreateSch, HasilPetaLokasiUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> HasilPetaLokasi | None:
        
        db_session = db_session or db.session
        
        query = select(HasilPetaLokasi).where(HasilPetaLokasi.id == id
                                                    ).options(selectinload(HasilPetaLokasi.details
                                                                            ).options(selectinload(HasilPetaLokasiDetail.bidang)
                                                                            ).options(selectinload(HasilPetaLokasiDetail.bidang_overlap))
                                                    ).options(selectinload(HasilPetaLokasi.bidang)
                                                    ).options(selectinload(HasilPetaLokasi.kjb_dt)
                                                    ).options(selectinload(HasilPetaLokasi.request_peta_lokasi)
                                                    ).options(selectinload(HasilPetaLokasi.planing
                                                                            ).options(selectinload(Planing.project)
                                                                            ).options(selectinload(Planing.desa))
                                                    ).options(selectinload(HasilPetaLokasi.skpt
                                                                            ).options(selectinload(Skpt.ptsk))
                                                    ).options(selectinload(HasilPetaLokasi.pemilik)
                                                    ).options(selectinload(HasilPetaLokasi.sub_project))
                                                    

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    async def get_by_bidang_id(
                    self, 
                    *, 
                    bidang_id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> HasilPetaLokasi | None:
        
        db_session = db_session or db.session
        query = select(HasilPetaLokasi).where(HasilPetaLokasi.bidang_id == bidang_id)

        response = await db_session.execute(query)

        return response.scalars().one_or_none()
    
    async def get_by_kjb_dt_id(
                    self, 
                    *, 
                    kjb_dt_id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> HasilPetaLokasi | None:
        
        db_session = db_session or db.session
        query = select(HasilPetaLokasi).where(HasilPetaLokasi.kjb_dt_id == kjb_dt_id)

        response = await db_session.execute(query)

        return response.scalars().one_or_none()

    async def get_by_id_for_cloud(
                    self, 
                    *, 
                    id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> HasilPetaLokasiUpdateCloud | None:
        
        db_session = db_session or db.session
        query = text(f"""
                    select
                    id,
                    bidang_id,
                    status_hasil_peta_lokasi,
                    hasil_analisa_peta_lokasi,
                    pemilik_id,
                    luas_surat,
                    planing_id,
                    sub_project_id,
                    skpt_id,
                    luas_ukur,
                    luas_nett,
                    luas_clear,
                    luas_gu_pt,
                    luas_gu_perorangan,
                    updated_by_id
                    from hasil_peta_lokasi
                    where id = '{str(id)}'
                    """)

        response = await db_session.execute(query)

        return response.fetchone()
    
hasil_peta_lokasi = CRUDHasilPetaLokasi(HasilPetaLokasi)