from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseGeoModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.mapping_model import (Mapping_Planing_PTSK_Desa, Mapping_Planing_PTSK_Desa_Rincik, Mapping_Planing_PTSK_Desa_Rincik_Bidang)

class DesaBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    luas:int

class DesaFullBase(BaseGeoModel, DesaBase):
    pass

class Desa(DesaFullBase, table=True):
    planing_ptsk_desa: "Mapping_Planing_PTSK_Desa" = Relationship(back_populates="desas")
    planing_ptsk_desa_rincik: "Mapping_Planing_PTSK_Desa_Rincik" = Relationship(back_populates="desas")
    planing_ptsk_desa_rincik_bidang: "Mapping_Planing_PTSK_Desa_Rincik_Bidang" = Relationship(back_populates="desas")

