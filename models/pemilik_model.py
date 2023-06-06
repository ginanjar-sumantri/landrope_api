from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING


class PemilikBase(SQLModel):
    name:str

class PemilikFullBase(BaseUUIDModel, PemilikBase):
    pass

class Pemilik(PemilikFullBase, table=True):
    kontaks:list["Kontak"] = Relationship(back_populates="pemilik", sa_relationship_kwargs={'lazy':'selectin'})


class KontakBase(SQLModel):
    nomor_telepon:str

class KontakFullBase(BaseUUIDModel, KontakBase):
    pass

class Kontak(KontakFullBase, table=True):
    pemilik: "Pemilik" = Relationship(back_populates="kontaks", sa_relationship_kwargs={'lazy':'selectin'})