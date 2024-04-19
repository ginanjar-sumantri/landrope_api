from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, text, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from typing import List
from common.ordered import OrderEnumSch
from common.enum import StatusLuasOverlapEnum, TipeOverlapEnum
from crud.base_crud import CRUDBase
from models import BidangOverlap, HasilPetaLokasiDetail, HasilPetaLokasi, Bidang
from schemas.bidang_overlap_sch import BidangOverlapCreateSch, BidangOverlapUpdateSch, BidangOverlapRawSch, BidangOverlapForPrintout
from uuid import UUID
from geoalchemy2 import functions

class CRUDBidangOverlap(CRUDBase[BidangOverlap, BidangOverlapCreateSch, BidangOverlapUpdateSch]):
    async def get_multi_by_override_bidang_id(
                        self,
                        *,
                        bidang_id:UUID, 
                        db_session : AsyncSession | None = None
                        ) -> List[BidangOverlap]:
        
        db_session = db_session or db.session
        
        query = select(BidangOverlap).where(BidangOverlap.parent_bidang_id == bidang_id)

        response =  await db_session.execute(query)
        return response.scalars().all()

    async def remove_multiple_data(self, *, list_obj: list[BidangOverlap],
                                   db_session: AsyncSession | None = None) -> None:
        db_session = db.session or db_session
        for i in list_obj:
            await db_session.delete(i)

    async def get_multi_by_bidang_id_for_printout(
                        self,
                        *,
                        bidang_id:UUID, 
                        db_session : AsyncSession | None = None
                        ) -> List[BidangOverlapForPrintout]:
        
        db_session = db_session or db.session
        
        query = text(f"""
                    select
                    distinct
                    bi.id as bidang_id,
                    Replace(bo.status_luas, '_', ' ') as ket,
                    Coalesce(pm.name, '') as nama,
                    bi.alashak,
                    bi.luas_surat as luas,
                    bo.luas as luas_overlap,
                    Coalesce(bo.kategori, '') as kat,
                    bi.id_bidang,
                    Replace(hpl.tipe_overlap, '_', ' ') as status_overlap
                    from bidang_overlap bo
                    inner join bidang bp on bp.id = bo.parent_bidang_id
                    inner join bidang bi on bi.id = bo.parent_bidang_intersect_id
                    left outer join hasil_peta_lokasi_detail hpl on hpl.bidang_overlap_id = bo.id
                    left outer join pemilik pm on pm.id = bi.pemilik_id
                    where bp.id = '{str(bidang_id)}'
                    and bo.is_show = true
                    """)
        

        response =  await db_session.execute(query)
        datas = response.fetchall()
        result = [BidangOverlapForPrintout(**dict(ov), 
                                        luasExt="{:,.0f}".format(ov["luas"]),
                                        luas_overlapExt="{:,.0f}".format(ov["luas_overlap"])) for ov in datas]
        return result
    
    async def get_multi_kulit_bintang_batal_by_petlok_id(
                        self,
                        *,
                        hasil_peta_lokasi_id:UUID, 
                        db_session : AsyncSession | None = None
                        ) -> List[BidangOverlap]:
        
        db_session = db_session or db.session
        
        query = select(BidangOverlap)
        query = query.join(HasilPetaLokasiDetail, BidangOverlap.id == HasilPetaLokasiDetail.bidang_overlap_id)
        query = query.join(HasilPetaLokasi, HasilPetaLokasi.id == HasilPetaLokasiDetail.hasil_peta_lokasi_id)
        query = query.filter(HasilPetaLokasi.id == hasil_peta_lokasi_id)
        query = query.filter(BidangOverlap.status_luas == StatusLuasOverlapEnum.Menambah_Luas)
        query = query.filter(HasilPetaLokasiDetail.tipe_overlap == TipeOverlapEnum.BintangBatal)

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_intersect_bidang(
            self, 
            *, 
            hasil_peta_lokasi_id:UUID | str,
            db_session : AsyncSession | None = None, 
            geom) -> list[BidangOverlap] | None:
        
        # g = shape(geom)
        # wkb = from_shape(g)

        db_session = db_session or db.session
        query = select(BidangOverlap)
        query = query.join(HasilPetaLokasiDetail, BidangOverlap.id == HasilPetaLokasiDetail.bidang_overlap_id)
        query = query.join(HasilPetaLokasi, HasilPetaLokasi.id == HasilPetaLokasiDetail.hasil_peta_lokasi_id)
        query = query.filter(HasilPetaLokasi.id == hasil_peta_lokasi_id)
        query = query.filter(BidangOverlap.status_luas == StatusLuasOverlapEnum.Menambah_Luas)
        query = query.filter(HasilPetaLokasiDetail.tipe_overlap == TipeOverlapEnum.BintangBatal)
        query = query.filter(functions.ST_IsValid(BidangOverlap.geom_temp) == True)
        query = query.filter(functions.ST_Intersects(BidangOverlap.geom_temp, geom))
        
        response =  await db_session.execute(query)
        
        return response.scalars().all()
    
    async def get_multi_by_parent_bidang_ids(self, *, list_parent_id:list[UUID]) -> list[BidangOverlap] | None :

        db_session = db.session

        query = select(BidangOverlap)
        query = query.where(BidangOverlap.parent_bidang_id.in_(list_parent_id))
        query = query.options(selectinload(BidangOverlap.bidang)
                    ).options(selectinload(BidangOverlap.bidang_intersect
                                ).options(selectinload(Bidang.pemilik))
                    )
        
        response = await db_session.execute(query)
        return response.scalars().all()

bidangoverlap = CRUDBidangOverlap(BidangOverlap)