from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.ptsk_model import Ptsk
    from models.desa_model import Desa
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang, Bidangoverlap

class MappingBase(SQLModel):
    pass

class Mapping_Planing_Ptsk(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id", primary_key=True)
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id", primary_key=True)

#--------------------------------------------------------------------------------------------------

class Mapping_Planing_Ptsk_Desa(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id", primary_key=True)
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id", primary_key=True)
    desa_id:UUID = Field(default=None, foreign_key="desa.id", primary_key=True)

#--------------------------------------------------------------------------------------------------

class Mapping_Planing_Ptsk_Desa_Rincik(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id", primary_key=True)
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id", primary_key=True)
    desa_id:UUID = Field(default=None, foreign_key="desa.id", primary_key=True)
    rincik_id:UUID = Field(default=None, foreign_key="rincik.id", primary_key=True)

#--------------------------------------------------------------------------------------------------

class Mapping_Planing_Ptsk_Desa_Rincik_Bidang(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id", primary_key=True)
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id", primary_key=True)
    desa_id:UUID = Field(default=None, foreign_key="desa.id", primary_key=True)
    rincik_id:UUID = Field(default=None, foreign_key="rincik.id", primary_key=True)
    bidang_id:UUID = Field(default=None, foreign_key="bidang.id", primary_key=True)

#--------------------------------------------------------------------------------------------------

class Mapping_Bidang_Overlap(MappingBase, table=True):
    bidang_id:UUID = Field(default=None, foreign_key="bidang.id", primary_key=True)
    bidang_overlap_id:UUID = Field(default=None, foreign_key="bidangoverlap.id", primary_key=True)

