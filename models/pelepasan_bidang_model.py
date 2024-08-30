from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import (Bidang, PelepasanHeader)

class PelepasanBidangBase(SQLModel):
    bidang_id: UUID = Field(nullable=False, foreign_key="bidang.id")
    pelepasan_header_id: UUID | None = Field(nullable=False, foreign_key="pelepasan_header.id")

class PelepasanBidangFullBase(PelepasanBidangBase, BaseUUIDModel):
    pass

class PelepasanBidang(PelepasanBidangFullBase, table=True):
    bidang:"Bidang" = Relationship(sa_relationship_kwargs={'lazy':'select'})

    @property
    def id_bidang(self) -> str | None:
        return self.bidang.id_bidang
    
    @property
    def alashak(self) -> str | None:
        return self.bidang.alashak
    
    @property
    def pemilik_name(self) -> str | None:
        return self.bidang.pemilik.name if self.bidang.pemilik else None
    
    @property
    def group(self) -> str | None:
        return self.bidang.group
    
    @property
    def luas_bayar(self) -> Decimal | None:
        return self.bidang.luas_bayar

   
