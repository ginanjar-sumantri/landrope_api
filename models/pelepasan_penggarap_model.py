from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import (PelepasanBidang, PelepasanHeader)


class PelepasanPenggarapBase(SQLModel):
    name: str | None = Field(nullable=True)
    alamat: str | None = Field(nullable=True)
    nomor_ktp: str | None = Field(nullable=True)
    nomor_handphone: int | None = Field(nullable=True)
    pelepasan_header_id: UUID = Field(nullable=False, foreign_key="pelepasan_header.id")

class PelepasanPenggarapFullBase(PelepasanPenggarapBase, BaseUUIDModel):
    pass

class PelepasanPenggarap(PelepasanPenggarapFullBase, table=True):
    pelepasan_bidang:"PelepasanBidang" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    pelepasan_header:"PelepasanHeader" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    