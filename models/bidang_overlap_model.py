from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal
from common.enum import StatusLuasOverlapEnum

if TYPE_CHECKING:
    from bidang_model import Bidang

class BidangOverlapBase(SQLModel):
    code:str | None
    parent_bidang_id:UUID = Field(foreign_key="bidang.id")
    parent_bidang_intersect_id:UUID = Field(foreign_key="bidang.id")
    luas:Decimal
    status_luas:StatusLuasOverlapEnum | None = Field(nullable=True)

class BidangOverlapRawBase(BaseUUIDModel, BidangOverlapBase):
    pass

class BidangOverlapFullBase(BaseGeoModel, BidangOverlapRawBase):
    pass

class BidangOverlap(BidangOverlapFullBase, table=True):
    bidang:"Bidang" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "joined",
                                "primaryjoin": "BidangOverlap.parent_bidang_id==Bidang.id"
                            }
    )

    bidang_intersect:"Bidang" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "joined",
                                "primaryjoin": "BidangOverlap.parent_bidang_intersect_id==Bidang.id"
                            }
    )


    @property
    def id_bidang_parent(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def id_bidang_intersect(self) -> str | None :
        return getattr(getattr(self, "bidang_intersect", None), "id_bidang", None)
    
    @property
    def alashak_parent(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def alashak_intersect(self) -> str | None :
        return getattr(getattr(self, "bidang_intersect", None), "alashak", None)