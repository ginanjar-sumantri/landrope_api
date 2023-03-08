from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.ptsk_model import PTSK
    from models.desa_model import Desa
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang, BidangOverlap

class MappingBase(BaseUUIDModel):
    pass

class Mapping_Planing_PTSK(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id")
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")

    planings:list["Planing"] = Relationship(back_populates="planing_ptsk")
    ptsks:list["PTSK"] = Relationship(back_populates="planing_ptsk")

#--------------------------------------------------------------------------------------------------

class Mapping_Planing_PTSK_Desa(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id")
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")
    desa_id:UUID = Field(default=None, foreign_key="desa.id")

    planings:list["Planing"] = Relationship(back_populates="planing_ptsk_desa")
    ptsks:list["PTSK"] = Relationship(back_populates="planing_ptsk_desa")
    desas:list["Desa"] = Relationship(back_populates="planing_ptsk_desa")

#--------------------------------------------------------------------------------------------------

class Mapping_Planing_PTSK_Desa_Rincik(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id")
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")
    desa_id:UUID = Field(default=None, foreign_key="desa.id")
    rincik_id:UUID = Field(default=None, foreign_key="rincik.id")

    planings:list["Planing"] = Relationship(back_populates="planing_ptsk_desa_rincik")
    ptsks:list["PTSK"] = Relationship(back_populates="planing_ptsk_desa_rincik")
    desas:list["Desa"] = Relationship(back_populates="planing_ptsk_desa_rincik")
    riciks:list["Rincik"] = Relationship(back_populates="planing_ptsk_desa_rincik")

#--------------------------------------------------------------------------------------------------

class Mapping_Planing_PTSK_Desa_Rincik_Bidang(MappingBase, table=True):
    planing_id:UUID = Field(default=None, foreign_key="planing.id")
    ptsk_id:UUID = Field(default=None, foreign_key="ptsk.id")
    desa_id:UUID = Field(default=None, foreign_key="desa.id")
    rincik_id:UUID = Field(default=None, foreign_key="rincik.id")
    bidang_id:UUID = Field(default=None, foreign_key="bidang.id")

    planings:list["Planing"] = Relationship(back_populates="planing_ptsk_desa_rincik_bidang")
    ptsks:list["PTSK"] = Relationship(back_populates="planing_ptsk_desa_rincik_bidang")
    desas:list["Desa"] = Relationship(back_populates="planing_ptsk_desa_rincik_bidang")
    riciks:list["Rincik"] = Relationship(back_populates="planing_ptsk_desa_rincik_bidang")
    bidangs:list["Bidang"] = Relationship(back_populates="planing_ptsk_desa_rincik_bidang")

#--------------------------------------------------------------------------------------------------

class Mapping_Bidang_Overlap(MappingBase, table=True):
    bidang_id:UUID = Field(default=None, foreign_key="bidang.id")
    bidang_overlap_id:UUID = Field(default=None, foreign_key="bidangoverlap.id")

    bidangs:list["Bidang"] = Relationship(back_populates="bidang_overlap")
    overlaps:list["BidangOverlap"] = Relationship(back_populates="bidang_overlap")
