from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.mapping_model import (Mapping_Planing_Ptsk, Mapping_Planing_Ptsk_Desa, Mapping_Planing_Ptsk_Desa_Rincik, 
                                  Mapping_Planing_Ptsk_Desa_Rincik_Bidang, Mapping_Bidang_Overlap)

class CRUDMappingPlaningPtsk(CRUDBase[Mapping_Planing_Ptsk]):
    pass

planing_ptsk = CRUDMappingPlaningPtsk(Mapping_Planing_Ptsk)

#-----------------------------------------------------------------------------------------------

class CRUDMappingPlaningPtskDesa(CRUDBase[Mapping_Planing_Ptsk_Desa]):
    pass

planing_ptsk_desa = CRUDMappingPlaningPtskDesa(Mapping_Planing_Ptsk_Desa)

#-----------------------------------------------------------------------------------------------

class CRUDMappingPlaningPtskDesaRincik(CRUDBase[Mapping_Planing_Ptsk_Desa_Rincik]):
    pass

planing_ptsk_desa_rincik = CRUDMappingPlaningPtskDesaRincik(Mapping_Planing_Ptsk_Desa_Rincik)

#-----------------------------------------------------------------------------------------------

class CRUDMappingPlaningPtskDesaRincikBidang(CRUDBase[Mapping_Planing_Ptsk_Desa_Rincik_Bidang]):
    pass

planing_ptsk_desa_rincik_bidang = CRUDMappingPlaningPtskDesaRincikBidang(Mapping_Planing_Ptsk_Desa_Rincik_Bidang)

#-----------------------------------------------------------------------------------------------

class CRUDMappingBidangOverlap(CRUDBase[Mapping_Bidang_Overlap]):
    pass

bidang_overlap = CRUDMappingBidangOverlap(Mapping_Bidang_Overlap)