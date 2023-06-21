from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import JenisAlashakEnum
from decimal import Decimal

if TYPE_CHECKING:
    from models.planing_model import Planing

class BebanBiaya(BaseUUIDModel, table=True):
    name:str
    is_active:bool

#####################################################

class JenisLahanBase(SQLModel):
    code:str = Field(max_length=50)
    name:str = Field(max_length=150)

class JenisLahan(BaseUUIDModel, JenisLahanBase, table=True):
    pass
    # bidangs: "Bidang" = Relationship(back_populates="jenis_lahan", sa_relationship_kwargs={'lazy':'selectin'})

######################################################

class JenisSurat(BaseUUIDModel, table=True):
    jenis_alashak:JenisAlashakEnum
    name:str

    # kjb_dts: list["KjbDt"] = Relationship(back_populates="jenis_surat", sa_relationship_kwargs={'lazy':'select'})
    # tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="jenis_surat", sa_relationship_kwargs={'lazy':'selectin'})
    
#######################################################

class HargaStandardBase(SQLModel):
    planing_id:UUID = Field(nullable=False, foreign_key="planing.id")
    harga:Decimal

class HargaStandard(BaseUUIDModel, HargaStandardBase, table=True):
    planing:"Planing" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def planing_name(self) -> str :
        if self.planing is None:
            return ""
        
        return self.planing.name
    
    @property
    def planing_code(self) -> str :
        if self.planing is None:
            return ""
        
        return self.planing.code