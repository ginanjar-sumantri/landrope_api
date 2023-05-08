from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang

class JenisLahanBase(SQLModel):
    code:str = Field(max_length=50)
    name:str = Field(max_length=150)

class JenisLahan(BaseUUIDModel, JenisLahanBase, table=True):
    rinciks: "Rincik" = Relationship(back_populates="jenis_lahan", sa_relationship_kwargs={'lazy':'selectin'})
    bidangs: "Bidang" = Relationship(back_populates="jenis_lahan", sa_relationship_kwargs={'lazy':'selectin'})
