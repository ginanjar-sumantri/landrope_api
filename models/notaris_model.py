from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.tanda_terima_notaris_model import TandaTerimaNotarisHd

class NotarisBase(SQLModel):
    name:str

class NotarisFullBase(BaseUUIDModel, NotarisBase):
    pass

class Notaris(NotarisFullBase, table=True):
    tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="notaris", sa_relationship_kwargs={'lazy':'selectin'})
    