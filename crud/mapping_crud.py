from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.mapping_model import (MappingPlaningPtsk, MappingBidangOverlap)

class CRUDMappingPlaningPtsk(CRUDBase[MappingPlaningPtsk]):
    pass

planing_ptsk = CRUDMappingPlaningPtsk(MappingPlaningPtsk)

#-----------------------------------------------------------------------------------------------

class CRUDMappingBidangOverlap(CRUDBase[MappingBidangOverlap]):
    pass

bidang_overlap = CRUDMappingBidangOverlap(MappingBidangOverlap)

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

