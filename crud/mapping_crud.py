from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from crud.base_crud import CRUDBase
from models.mapping_model import (MappingPlaningSkpt, MappingBidangOverlap)
from schemas.mapping_sch import MappingPlaningSkptSch

class CRUDMappingPlaningPtsk(CRUDBase[MappingPlaningSkpt, MappingPlaningSkptSch, MappingPlaningSkptSch]):
    async def get_mapping_by_plan_sk_id(self, *, sk_id: UUID | str, plan_id: UUID | str, 
                  db_session: AsyncSession | None = None) -> MappingPlaningSkpt | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.planing_id == plan_id, self.model.skpt_id == sk_id))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

planing_skpt = CRUDMappingPlaningPtsk(MappingPlaningSkpt)

#-----------------------------------------------------------------------------------------------

# class CRUDMappingBidangOverlap(CRUDBase[MappingBidangOverlap]):
#     pass

# bidang_overlap = CRUDMappingBidangOverlap(MappingBidangOverlap)

#-----------------------------------------------------------------------------------------------

# class CRUDMappingPlaningPtskDesa(CRUDBase[Mapping_Planing_Ptsk_Desa]):
#     pass

# planing_ptsk_desa = CRUDMappingPlaningPtskDesa(Mapping_Planing_Ptsk_Desa)

#-----------------------------------------------------------------------------------------------

# class CRUDMappingPlaningPtskDesaRincik(CRUDBase[Mapping_Planing_Ptsk_Desa_Rincik]):
#     pass

# planing_ptsk_desa_rincik = CRUDMappingPlaningPtskDesaRincik(Mapping_Planing_Ptsk_Desa_Rincik)

#-----------------------------------------------------------------------------------------------

# class CRUDMappingPlaningPtskDesaRincikBidang(CRUDBase[Mapping_Planing_Ptsk_Desa_Rincik_Bidang]):
#     pass

# planing_ptsk_desa_rincik_bidang = CRUDMappingPlaningPtskDesaRincikBidang(Mapping_Planing_Ptsk_Desa_Rincik_Bidang)

#-----------------------------------------------------------------------------------------------

