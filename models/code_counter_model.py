from sqlmodel import SQLModel
from models.base_model import BaseUUIDModel, BaseGeoModel
from decimal import Decimal
from enum import Enum

class CodeCounterEnum(str, Enum):
    Desa = "Desa"
    Dokumen = "Dokumen"

class CodeCounterBase(SQLModel):
    entity:CodeCounterEnum | None
    last:int | None

class CodeCounter(BaseUUIDModel, CodeCounterBase, table=True):
    pass
