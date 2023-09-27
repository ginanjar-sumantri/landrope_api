from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy import exc
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.hasil_peta_lokasi_model import HasilPetaLokasi, HasilPetaLokasiDetail
from schemas.hasil_peta_lokasi_sch import HasilPetaLokasiCreateSch, HasilPetaLokasiUpdateSch, HasilPetaLokasiCreateExtSch
from typing import List
from uuid import UUID
from datetime import datetime

class CRUDHasilPetaLokasi(CRUDBase[HasilPetaLokasi, HasilPetaLokasiCreateSch, HasilPetaLokasiUpdateSch]):
    
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

    async def get_by_id(
                    self, 
                    *, 
                    kjb_dt_id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> HasilPetaLokasi | None:
        
        db_session = db_session or db.session
        query = select(HasilPetaLokasi).where(HasilPetaLokasi.kjb_dt_id == kjb_dt_id)

        response = await db_session.execute(query)

        return response.fetchone
    
hasil_peta_lokasi = CRUDHasilPetaLokasi(HasilPetaLokasi)