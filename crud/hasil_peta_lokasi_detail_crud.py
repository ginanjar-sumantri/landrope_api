from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import HasilPetaLokasiDetail, Bidang
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailCreateSch, HasilPetaLokasiDetailUpdateSch, HasilPetaLokasiDetailForUtj
from typing import List
from uuid import UUID

class CRUDHasilPetaLokasiDetail(CRUDBase[HasilPetaLokasiDetail, HasilPetaLokasiDetailCreateSch, HasilPetaLokasiDetailUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> HasilPetaLokasiDetail | None:
        
        db_session = db_session or db.session
        
        query = select(HasilPetaLokasiDetail).where(HasilPetaLokasiDetail.id == id
                                                    ).options(selectinload(HasilPetaLokasiDetail.hasil_peta_lokasi)
                                                    ).options(selectinload(HasilPetaLokasiDetail.bidang
                                                                            ).options(selectinload(Bidang.pemilik))
                                                    ).options(selectinload(HasilPetaLokasiDetail.bidang_overlap))
                                                   
                                                    

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_data_removed_by_hasil_peta_lokasi_id(
            self, 
            *, 
            hasil_peta_lokasi_id:UUID | str,
            hasil_peta_lokasi_detail_ids:list[UUID],
            db_session : AsyncSession | None = None) -> List[HasilPetaLokasiDetail] | None:
        
        db_session = db_session or db.session

        query = select(self.model
                       ).where(self.model.hasil_peta_lokasi_id == hasil_peta_lokasi_id
                               ).filter(~self.model.id.in_(hasil_peta_lokasi_detail_ids))

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_by_hasil_peta_lokasi_id(
            self, 
            *, 
            hasil_peta_lokasi_id:UUID | str, 
            db_session : AsyncSession | None = None) -> List[HasilPetaLokasiDetail] | None:
        
        db_session = db_session or db.session

        query = select(self.model).where(self.model.hasil_peta_lokasi_id == hasil_peta_lokasi_id
                                ).options(selectinload(HasilPetaLokasiDetail.bidang_overlap))

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_keterangan_by_bidang_id_for_printout_utj(
            self, 
            *, 
            bidang_id:UUID | str, 
            db_session : AsyncSession | None = None) -> List[HasilPetaLokasiDetailForUtj] | None:
        
        db_session = db_session or db.session

        query = text(f"""
                    select
                    hpl_dt.id,
                    hpl_dt.keterangan
                    from hasil_peta_lokasi_detail hpl_dt
                    inner join hasil_peta_lokasi hpl on hpl.id = hpl_dt.hasil_peta_lokasi_id
                    inner join bidang b on b.id = hpl.bidang_id
                    where b.id = '{str(bidang_id)}'
                    """)

        response =  await db_session.execute(query)
        return response.fetchall()
    
    async def remove_multiple_data(self, *, list_obj: list[HasilPetaLokasiDetail],
                                   db_session: AsyncSession | None = None) -> None:
        db_session = db.session or db_session
        for i in list_obj:
            await db_session.delete(i)

hasil_peta_lokasi_detail = CRUDHasilPetaLokasiDetail(HasilPetaLokasiDetail)