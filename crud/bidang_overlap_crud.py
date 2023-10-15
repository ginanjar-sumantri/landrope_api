from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from typing import List
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.bidang_overlap_model import BidangOverlap
from schemas.bidang_overlap_sch import BidangOverlapCreateSch, BidangOverlapUpdateSch, BidangOverlapRawSch, BidangOverlapForPrintout
from uuid import UUID

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
                    inner join hasil_peta_lokasi_detail hpl on hpl.bidang_overlap_id = bo.id
                    left outer join pemilik pm on pm.id = bi.pemilik_id
                    where bp.id = '{str(bidang_id)}'
                    """)

        response =  await db_session.execute(query)
        datas = response.fetchall()
        result = [BidangOverlapForPrintout(**dict(ov), 
                                        luasExt="{:,.0f}".format(ov["luas"]),
                                        luas_overlapExt="{:,.0f}".format(ov["luas_overlap"])) for ov in datas]
        return result

bidangoverlap = CRUDBidangOverlap(BidangOverlap)