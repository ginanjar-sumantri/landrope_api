from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import (Bidang, PeminjamanHeader)

class PeminjamanBidangBase(SQLModel):
    bidang_id: UUID | None = Field(nullable=True, foreign_key="bidang.id")
    peminjaman_header_id: UUID | None = Field(nullable=True, foreign_key="peminjaman_header.id")

class PeminjamanBidangFullBase(PeminjamanBidangBase, BaseUUIDModel):
    pass

class PeminjamanBidang(PeminjamanBidangFullBase, table=True):
    bidang:"Bidang" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    peminjaman_header:"PeminjamanHeader" = Relationship(back_populates="peminjaman_bidangs", sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def id_bidang(self):
        self.bidang.id_bidang
    
    # @property
    # def id_bidang(self):
    #     self.bidang.id_bidang


    
