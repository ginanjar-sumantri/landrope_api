from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.rincik_model import Rincik

class JenisLahan(BaseUUIDModel, table=True):
    code:str = Field(max_length=50)
    name:str = Field(max_length=150)

    rincik: "Rincik" = Relationship(back_populates="jenislahan")


