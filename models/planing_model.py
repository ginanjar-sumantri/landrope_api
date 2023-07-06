from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.bidang_model import Bidang
    from models.project_model import Project
    from models.desa_model import Desa
    from models.bundle_model import BundleHd

class PlaningBase(SQLModel):
    project_id: UUID = Field(default=None, foreign_key="project.id")
    desa_id:UUID = Field(default=None, foreign_key="desa.id")
    luas:Decimal
    name:str | None = Field(nullable=True, max_length=100)
    code:str | None = Field(nullable=True, max_length=50)

class PlaningRawBase(BaseUUIDModel, PlaningBase):
    pass

class PlaningFullBase(PlaningRawBase, BaseGeoModel):
    pass

class Planing(PlaningFullBase, table=True):

    project:"Project" = Relationship(back_populates="project_planings", sa_relationship_kwargs={'lazy':'selectin'})
    desa:"Desa" = Relationship(back_populates="desa_planings", sa_relationship_kwargs={'lazy':'selectin'})
    bidangs: list["Bidang"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'selectin'})
    bundlehds: list["BundleHd"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'select'})
    # kjb_dts: list["KjbDt"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'select'})
    # kjb_dts_by_ttn: list["KjbDt"] = Relationship(back_populates="planing_by_ttn", sa_relationship_kwargs={'lazy':'select'})
    # tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="planing", sa_relationship_kwargs={'lazy':'selectin'})
    

    @property
    def project_name(self)-> str:
        if self.project is None:
            return ""
        return self.project.name
    
    @property
    def desa_name(self)-> str:
        if self.desa is None:
            return ""
        return self.desa.name
    
    @property
    def section_name(self)-> str:
        if self.project is None:
            return ""
        if self.project.section is None:
            return ""
        return self.project.section.name