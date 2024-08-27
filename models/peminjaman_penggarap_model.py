from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import (PeminjamanHeader)


class PeminjamanPenggarapBase(SQLModel):
    name: str | None = Field(nullable=True)
    alamat: str | None = Field(nullable=True)
    nomor_ktp: str | None = Field(nullable=True)
    nomor_handphone: int | None = Field(nullable=True)
    peminjaman_header_id: UUID = Field(nullable=False, foreign_key="peminjaman_header.id")

class PeminjamanPenggarapFullBase(PeminjamanPenggarapBase, BaseUUIDModel):
    pass

class PeminjamanPenggarap(PeminjamanPenggarapFullBase, table=True):
    peminjaman_header:"PeminjamanHeader" = Relationship(back_populates="peminjaman_bidangs", sa_relationship_kwargs={'lazy':'selectin'})

    