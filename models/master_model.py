from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import JenisAlashakEnum

if TYPE_CHECKING:
    from models.bidang_model import Bidang
    from models.kjb_model import KjbDt

class Beban(BaseUUIDModel, table=True):
    name:str
    is_active:bool

#####################################################

class JenisLahanBase(SQLModel):
    code:str = Field(max_length=50)
    name:str = Field(max_length=150)

class JenisLahan(BaseUUIDModel, JenisLahanBase, table=True):
    bidangs: "Bidang" = Relationship(back_populates="jenis_lahan", sa_relationship_kwargs={'lazy':'selectin'})

######################################################

class JenisSurat(BaseUUIDModel, table=True):
    jenis_alashak:JenisAlashakEnum
    name:str

    kjb_dts: list["KjbDt"] = Relationship(back_populates="jenis_surat", sa_relationship_kwargs={'lazy':'select'})
    