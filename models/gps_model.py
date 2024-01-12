from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from decimal import Decimal
from enum import Enum
from uuid import UUID
from typing import TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
    from models import Skpt, Worker, Planing

class StatusGpsEnum(str, Enum):
    Masuk_SK_Clear = "Masuk_SK_Clear"
    Masuk_SK_Overlap = "Masuk_SK_Overlap"
    Tidak_Masuk_SK_Clear = "Tidak_Masuk_SK_Clear"
    Tidak_Masuk_SK_Overlap = "Tidak_Masuk_SK_Overlap"

class GpsBase(SQLModel):
    nama:str|None = Field(nullable=True) #pemilik
    alashak:str|None = Field(nullable=True) #surat
    luas:Decimal|None = Field(nullable=True)
    penunjuk:str|None = Field(nullable=True)
    pic:str|None = Field(nullable=True)
    group:str|None = Field(nullable=True)
    status:StatusGpsEnum|None = Field(nullable=True)
    skpt_id:UUID|None = Field(default=None, nullable=True, foreign_key="skpt.id")
    tanggal:date|None = Field(nullable=True)
    planing_id:UUID|None = Field(nullable=True, foreign_key="planing.id")
    remark:str|None = Field(nullable=True)

class GpsRawBase(BaseUUIDModel, GpsBase):
    pass

class GpsFullBase(BaseGeoModel, GpsRawBase):
    pass

class Gps(GpsFullBase, table=True):
    skpt:"Skpt" = Relationship(
        sa_relationship_kwargs=
        {
            'lazy':'select'
        }
    )

    planing:"Planing" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Gps.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def ptsk_name(self)-> str | None:
        return getattr(getattr(getattr(self, 'skpt', None), 'ptsk', None), 'name', None)
    
    @property
    def ptsk_id(self)-> UUID | None:
        return getattr(getattr(getattr(self, 'skpt', None), 'ptsk', None), 'id', None)
    
    @property
    def nomor_sk(self)-> str:
        return getattr(getattr(self, 'skpt', None), 'nomor_sk', None)
    
    @property
    def planing_name(self)-> str:
        return getattr(getattr(self, 'planing', None), 'name', None)
    
    @property
    def desa_name(self)-> str:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), 'name', None)
    
    @property
    def project_name(self)-> str:
        return getattr(getattr(getattr(self, 'planing', None), 'project', None), 'name', None)