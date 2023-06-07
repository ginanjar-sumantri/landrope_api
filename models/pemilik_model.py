from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.kjb_model import KjbHd

class PemilikBase(SQLModel):
    name:str

class PemilikFullBase(BaseUUIDModel, PemilikBase):
    pass

class Pemilik(PemilikFullBase, table=True):
    kontaks:list["Kontak"] = Relationship(back_populates="pemilik", sa_relationship_kwargs={'lazy':'selectin'})
    rekenings:list["Rekening"] = Relationship(back_populates="pemilik", sa_relationship_kwargs={'lazy':'selectin'})
    kjb_hds: list["KjbHd"] = Relationship(back_populates="pemilik", sa_relationship_kwargs={'lazy':'select'})


class KontakBase(SQLModel):
    nomor_telepon:str
    pemilik_id:UUID = Field(foreign_key="pemilik.id", nullable=False)

class KontakFullBase(BaseUUIDModel, KontakBase):
    pass

class Kontak(KontakFullBase, table=True):
    pemilik: "Pemilik" = Relationship(back_populates="kontaks", sa_relationship_kwargs={'lazy':'select'})


class RekeningBase(SQLModel):
    nama_pemilik_rekening:str
    bank_rekening:str
    nomor_rekening:str

    pemilik_id:UUID = Field(foreign_key="pemilik.id", nullable=False)

class RekeningFullBase(BaseUUIDModel, RekeningBase):
    pass

class Rekening(RekeningFullBase, table=True):
    pemilik: "Pemilik" = Relationship(back_populates="rekenings", sa_relationship_kwargs={'lazy':'select'})