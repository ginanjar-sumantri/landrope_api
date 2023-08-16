from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.hasil_peta_lokasi_model import HasilPetaLokasiDetail
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailCreateSch, HasilPetaLokasiDetailUpdateSch
from typing import List
from uuid import UUID

class CRUDHasilPetaLokasiDetail(CRUDBase[HasilPetaLokasiDetail, HasilPetaLokasiDetailCreateSch, HasilPetaLokasiDetailUpdateSch]):
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

        query = select(self.model).where(self.model.hasil_peta_lokasi_id == hasil_peta_lokasi_id)

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def remove_multiple_data(self, *, list_obj: list[HasilPetaLokasiDetail],
                                   db_session: AsyncSession | None = None) -> None:
        db_session = db.session or db_session
        for i in list_obj:
            await db_session.delete(i)

hasil_peta_lokasi_detail = CRUDHasilPetaLokasiDetail(HasilPetaLokasiDetail)