from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from models.checklist_dokumen_model import ChecklistDokumen
    from models.bundle_model import BundleDt
    from models.tanda_terima_notaris_model import TandaTerimaNotarisDt
    from models.worker_model import Worker


class DokumenBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=100)
    dyn_form:Optional[str]
    is_keyword:Optional[bool] #apakah dokumen tersebut masuk dalam pencarian
    key_field:Optional[str] #key apa yang dipakai dan diambil valuenya untuk jadi keyword
    is_riwayat: Optional[bool] #apakah dokumen tersebut memiliki riwayat
    key_riwayat:Optional[str] #key unik yang dipakai untuk crud pada riwayat tersebut
    kategori_dokumen_id:UUID | None = Field(nullable=True, foreign_key="kategori_dokumen.id")
    additional_info:Optional[str] = Field(nullable=True)
    is_multiple:bool|None = Field(nullable=True)
    is_active:bool|None = Field(nullable=True)
    is_exclude_printout:bool|None = Field(nullable=True)

class DokumenFullBase(BaseUUIDModel, DokumenBase):
    pass

class Dokumen(DokumenFullBase, table=True):
    bundledts:list["BundleDt"] = Relationship(back_populates="dokumen", sa_relationship_kwargs={'lazy':'select'})
    cheklistdokumens:list["ChecklistDokumen"] = Relationship(back_populates="dokumen", sa_relationship_kwargs={'lazy':'select'})

    tanda_terima_notaris_dts:list["TandaTerimaNotarisDt"] = Relationship(back_populates="dokumen", sa_relationship_kwargs={'lazy':'select'})
    kategori_dokumen:"KategoriDokumen" = Relationship(
        back_populates="dokumens",
        sa_relationship_kwargs={'lazy':'select'})
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Dokumen.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def kategori_dokumen_name(self) -> str | None:
        return getattr(getattr(self, 'kategori_dokumen', None), 'name', None)
    

class KategoriDokumenBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=100)
    fg_active:bool | None

class KategoriDokumenFullBase(BaseUUIDModel, KategoriDokumenBase):
    pass

class KategoriDokumen(KategoriDokumenFullBase, table=True):
    dokumens:list["Dokumen"] = Relationship(
        back_populates="kategori_dokumen", 
        sa_relationship_kwargs={'lazy':'select'})
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "KategoriDokumen.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
