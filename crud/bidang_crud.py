from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy import text
from typing import List
from crud.base_crud import CRUDBase
from models.bidang_model import Bidang
from models.skpt_model import Skpt
from models.ptsk_model import Ptsk
from models.planing_model import Planing
from models.desa_model import Desa
from models.project_model import Project
from schemas.bidang_sch import BidangCreateSch, BidangUpdateSch, BidangShpSch, BidangShpExSch, BidangRawSch, BidangGetAllSch, BidangForTreeReportSch
from common.exceptions import (IdNotFoundException, NameNotFoundException, ImportFailedException, FileNotFoundException)
from common.enum import StatusBidangEnum
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
                       ).where(and_(self.model.id != id, 
                                    functions.ST_IsValid(self.model.geom) == True,
                                    self.model.status != StatusBidangEnum.Batal)
                               ).filter(functions.ST_Intersects(self.model.geom, geom))
        
        response =  await db_session.execute(query)
        
        return response.scalars().all()
    
    async def get_all_bidang_order_gu(self, *, db_session : AsyncSession | None = None, query : Bidang | Select[Bidang]| None = None) -> List[BidangGetAllSch] | None:
        db_session = db_session or db.session
        if query is None:
            query = select(self.model)
        response =  await db_session.execute(query)
        return response.scalars().all()
        
    async def get_all_bidang_tree_report_map(
            self, 
            *,
            project_id:UUID,
            desa_id:UUID,
            ptsk_id:UUID,
            db_session : AsyncSession | None = None, 
            query : Bidang | Select[Bidang]| None = None
            ):
       
    
        db_session = db_session or db.session
        query = select(Bidang.id,
                       Bidang.id_bidang,
                       Bidang.id_bidang_lama,
                       Bidang.alashak,
                       Ptsk.id.label("ptsk_id"),
                       Ptsk.name.label("ptsk_name"),
                       Desa.id.label("desa_id"),
                       Desa.name.label("desa_name"),
                       Project.id.label("project_id"),
                       Project.name.label("project_name")
                       ).select_from(Bidang
                                    ).join(Skpt, Bidang.skpt_id == Skpt.id
                                    ).join(Ptsk, Skpt.ptsk_id == Ptsk.id
                                    ).join(Planing, Bidang.planing_id == Planing.id
                                    ).join(Desa, Planing.desa_id == Desa.id
                                    ).join(Project, Planing.project_id == Project.id
                                    ).where(and_(
                                        Project.id == project_id,
                                        Desa.id == desa_id,
                                        
                                    )).order_by(text("id_bidang asc"))
        
        if ptsk_id == UUID("00000000-0000-0000-0000-000000000000"):
            query = query.where(Bidang.skpt_id == None)
        else:
            query = query.where(Ptsk.id == ptsk_id)
        
        response =  await db_session.execute(query)
        return response.fetchall()

bidang = CRUDBidang(Bidang)