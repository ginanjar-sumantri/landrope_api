from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseGeoModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.project_model import Project
    from models.mapping_model import (Mapping_Planing_PTSK, Mapping_Planing_PTSK_Desa, 
                                      Mapping_Planing_PTSK_Desa_Rincik, Mapping_Planing_PTSK_Desa_Rincik_Bidang)

class PlaningBase(SQLModel):
    project_id: UUID = Field(default=None, foreign_key="project.id")
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)

class PlaningFullBase(BaseGeoModel, PlaningBase):
    pass

class Planing(PlaningFullBase, table=True):
    project: "Project" = Relationship(back_populates="planings")
    planing_ptsk: "Mapping_Planing_PTSK" = Relationship(back_populates="planings")
    planing_ptsk_desa: "Mapping_Planing_PTSK_Desa" = Relationship(back_populates="planings")
    planing_ptsk_desa_rincik: "Mapping_Planing_PTSK_Desa_Rincik" = Relationship(back_populates="planings")
    planing_ptsk_desa_rincik_bidang: "Mapping_Planing_PTSK_Desa_Rincik_Bidang" = Relationship(back_populates="planings")