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
from models import KjbBebanBiaya, KjbDt, HasilPetaLokasi, BebanBiaya
from schemas.kjb_beban_biaya_sch import KjbBebanBiayaCreateSch, KjbBebanBiayaUpdateSch, KjbBebanBiayaSch
from schemas.beban_biaya_sch import BebanBiayaForSpkSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDKjbBebanBiaya(CRUDBase[KjbBebanBiaya, KjbBebanBiayaCreateSch, KjbBebanBiayaUpdateSch]):
    async def get_by_id(self, *, 
                  id:UUID|str,
                  db_session: AsyncSession | None = None) -> KjbBebanBiaya | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(self.model.id == id).options(selectinload(KjbBebanBiaya.beban_biaya))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_beban_pembeli_by_kjb_hd_id(self, *, 
                  kjb_hd_id: UUID | str,
                  db_session: AsyncSession | None = None) -> List[KjbBebanBiayaSch] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.kjb_hd_id == kjb_hd_id, self.model.beban_pembeli == True)
                                        ).options(selectinload(KjbBebanBiaya.beban_biaya))
        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_by_kjb_hd_id_and_beban_biaya_id(self, *, 
                  kjb_hd_id: UUID | str,
                  beban_biaya_id:UUID | str,
                  db_session: AsyncSession | None = None) -> KjbBebanBiaya | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.kjb_hd_id == kjb_hd_id, self.model.beban_biaya_id == beban_biaya_id))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_kjb_beban_by_kjb_hd_id(self, *, 
                  kjb_hd_id: UUID | str,
                  jenis_alashak:JenisAlashakEnum,
                  db_session: AsyncSession | None = None) -> List[BebanBiayaForSpkSch] | None:
        
        db_session = db_session or db.session
        query = select(KjbBebanBiaya)
        query = query.join(BebanBiaya, BebanBiaya.id == KjbBebanBiaya.beban_biaya_id)
        query = query.filter(self.model.kjb_hd_id == kjb_hd_id)

        if jenis_alashak == JenisAlashakEnum.Girik:
            query = query.filter(BebanBiaya.default_spk_girik)
        else:
            query = query.filter(BebanBiaya.default_spk_sertifikat)

        query = query.options(selectinload(KjbBebanBiaya.beban_biaya))
        
        response = await db_session.execute(query)

        return response.scalars().all()

    async def get_kjb_beban_by_bidang_id(self, *, 
                  bidang_id: UUID | str,
                  db_session: AsyncSession | None = None) -> List[BebanBiayaForSpkSch] | None:
        
        db_session = db_session or db.session

        query = select(KjbBebanBiaya)
        query = query.join(KjbDt, KjbDt.kjb_hd_id == KjbBebanBiaya.kjb_hd_id)
        query = query.join(HasilPetaLokasi, HasilPetaLokasi.kjb_dt_id == KjbDt.id)
        query = query.where(HasilPetaLokasi.bidang_id == bidang_id)
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
kjb_bebanbiaya = CRUDKjbBebanBiaya(KjbBebanBiaya)