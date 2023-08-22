from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from typing import List
from crud.base_crud import CRUDBase
from models.bidang_model import Bidang
from schemas.bidang_sch import BidangCreateSch, BidangUpdateSch, BidangShpSch, BidangShpExSch, BidangRawSch, BidangGetAllSch
from common.exceptions import (IdNotFoundException, NameNotFoundException, ImportFailedException, FileNotFoundException)
from services.gcloud_storage_service import GCStorageService
from services.geom_service import GeomService
from io import BytesIO
from uuid import UUID
from geoalchemy2 import functions
from shapely.geometry import shape
from geoalchemy2.shape import from_shape


class CRUDBidang(CRUDBase[Bidang, BidangCreateSch, BidangUpdateSch]):
    async def get_by_id_bidang(
        self, *, idbidang: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang == idbidang))
        return obj.scalar_one_or_none()
    
    async def get_by_id_bidang_lama(
        self, *, idbidang_lama: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang_lama == idbidang_lama))
        return obj.scalar_one_or_none()
    
    async def get_by_id_bidang_id_bidang_lama(
        self, *, idbidang: str, idbidang_lama: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(and_(Bidang.id_bidang == idbidang, Bidang.id_bidang_lama == idbidang_lama)))
        return obj.scalar_one_or_none()
    
    async def get_intersect_bidang(
            self, 
            *, 
            id:UUID | str,
            db_session : AsyncSession | None = None, 
            geom) -> list[Bidang] | None:
        
        # g = shape(geom)
        # wkb = from_shape(g)

        db_session = db_session or db.session
        query = select(self.model
                       ).where(and_(self.model.id != id, functions.ST_IsValid(self.model.geom) == True)
                               ).filter(functions.ST_Intersects(self.model.geom, geom))
        
        response =  await db_session.execute(query)
        
        return response.scalars().all()
    
    async def get_all_bidang_order_gu(self, *, db_session : AsyncSession | None = None, query : Bidang | Select[Bidang]| None = None) -> List[BidangGetAllSch] | None:
        db_session = db_session or db.session
        if query is None:
            query = select(self.model)
        response =  await db_session.execute(query)
        return response.scalars().all()
        


bidang = CRUDBidang(Bidang)