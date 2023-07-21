from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional

class KategoriBase(SQLModel):
    name:str = Field(nullable=False)

class KategoriFullBase(BaseUUIDModel, KategoriBase):
    pass

class Kategori(KategoriFullBase, table=True):
    kategori_subs:list["KategoriSub"] = Relationship(sa_relationship_kwargs={'lazy':'selectin'})


class KategoriSubBase(SQLModel):
    name:str = Field(nullable=False)
    kategori_id:UUID = Field(nullable=False, foreign_key="kategori.id")

class KategoriSubFullBase(BaseUUIDModel, KategoriSubBase):
    pass

class KategoriSub(KategoriSubFullBase, table=True):
    kategori:"Kategori" = Relationship(back_populates="kategori_subs", sa_relationship_kwargs={'lazy' : 'selectin'})



class KategoriProyekBase(SQLModel):
    name:str = Field(nullable=False)

class KategoriProyekFullBase(BaseUUIDModel, KategoriProyekBase):
    pass

class KategoriProyek(KategoriProyekFullBase, table=True):
    pass