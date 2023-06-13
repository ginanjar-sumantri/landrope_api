from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.checklist_dokumen_model import ChecklistDokumen
    from models.bundle_model import BundleDt


class DokumenBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=100)
    dyn_form:str | None
    is_keyword:bool | None #apakah dokumen tersebut masuk dalam pencarian
    key_field:str | None = Field(nullable=True)

class DokumenFullBase(BaseUUIDModel, DokumenBase):
    pass

class Dokumen(DokumenFullBase, table=True):
    bundledts:list["BundleDt"] = Relationship(back_populates="dokumen", sa_relationship_kwargs={'lazy':'select'})
    cheklistdokumens:list["ChecklistDokumen"] = Relationship(back_populates="dokumen", sa_relationship_kwargs={'lazy':'select'})



