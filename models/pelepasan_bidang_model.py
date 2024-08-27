from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import (Bidang, PelepasanHeader)

class PelepasanBidangBase(SQLModel):
    bidang_id: UUID = Field(nullable=False, foreign_key="bidang.id")
    pelepasan_header_id: UUID = Field(nullable=False, foreign_key="pelepasan_header.id")

    
class PelepasanBidangFullBase(PelepasanBidangBase, BaseUUIDModel):
    pass

class PelepasanBidang(PelepasanBidangFullBase, table=True):
    bidang:"Bidang" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    pelepasan_header:"PelepasanHeader" = Relationship(back_populates="pelepasan_bidangs", sa_relationship_kwargs={'lazy':'selectin'})

   
