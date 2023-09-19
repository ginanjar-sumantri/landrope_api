from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import TanggunganBiayaEnum
from uuid import UUID
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bidang_model import Bidang
    from master_model import BebanBiaya
    from worker_model import Worker

class BidangKomponenBiayaBase(SQLModel):
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
    beban_pembeli:Optional[bool] = Field(nullable=True)
    is_use:Optional[bool] = Field(nullable=True, default=False)
    is_paid:Optional[bool] = Field(nullable=True, default=False)
    

class BidangKomponenBiayaFullBase(BaseUUIDModel, BidangKomponenBiayaBase):
    pass

class BidangKomponenBiaya(BidangKomponenBiayaFullBase, table=True):
    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    beban_biaya:"BebanBiaya" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "BidangKomponenBiaya.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def beban_biaya_name(self) -> str :
        return getattr(getattr(self, 'beban_biaya', None), 'name', None)


