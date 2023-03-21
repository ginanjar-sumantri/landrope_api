from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.rincik_model import Rincik

class JenisLahanBase(SQLModel):
    code:str = Field(max_length=50)
    name:str = Field(max_length=150)

class JenisLahan(BaseUUIDModel, JenisLahanBase, table=True):
    rinciks: "Rincik" = Relationship(back_populates="jenis_lahan")
