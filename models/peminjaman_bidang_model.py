from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models import (Bidang, PeminjamanHeader)

class PeminjamanBidangBase(SQLModel):
    bidang_id: UUID | None = Field(nullable=True, foreign_key="bidang.id")
    peminjaman_header_id: UUID | None = Field(nullable=True, foreign_key="peminjaman_header.id")

class PeminjamanBidangFullBase(PeminjamanBidangBase, BaseUUIDModel):
    pass

class PeminjamanBidang(PeminjamanBidangFullBase, table=True):
    bidang:"Bidang" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    peminjaman_header:"PeminjamanHeader" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

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

    


    
