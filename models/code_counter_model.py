from sqlmodel import SQLModel, Field
from models.base_model import BaseUUIDModel, BaseGeoModel
from decimal import Decimal

from enum import Enum

class CodeCounterEnum(str, Enum):
    Desa = "Desa"
    Dokumen = "Dokumen"
    Bundle = "Bundle"
    Kjb = "Kjb"
    BidangOverlap = "BidangOverlap"
    RequestPetaLokasi = "RequestPetaLokasi"
    OrderGambarUkur = "OrderGambarUkur"
    Spk = "Spk"
    Utj = "Utj"
    Dp = "Dp"
    Lunas = "Lunas"

class CodeCounterBase(SQLModel):
    entity:CodeCounterEnum | None
    last:int | None = Field(default=1, nullable=True)
    digit:int | None = Field(default=3, nullable=True)


class CodeCounter(BaseUUIDModel, CodeCounterBase, table=True):
    pass
