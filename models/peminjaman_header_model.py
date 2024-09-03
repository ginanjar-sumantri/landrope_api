from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, List
from common.enum import (KategoriTipeTanahEnum)
from datetime import date

if TYPE_CHECKING:
    from models import (Worker, Ptsk, PeminjamanBidang, PeminjamanPenggarap, Project, Desa, Ptsk)

class PeminjamanHeaderBase(SQLModel):
    nomor_perjanjian: str | None = Field(nullable=False)
    tanggal_perjanjian: date | None = Field(nullable=True)
    tanggal_berakhir: date | None = Field(nullable=True)
    kategori: KategoriTipeTanahEnum = Field(nullable=True)

    ptsk_id: UUID | None = Field(nullable=True, foreign_key="ptsk.id")
    project_id: UUID | None = Field(nullable=True, foreign_key="project.id")
    desa_id: UUID | None = Field(nullable=True, foreign_key="desa.id")

    tanda_tangan_lurah: bool | None = Field(nullable=True)
    produktivitas_tanah: bool | None = Field(nullable=True)
    gratis: bool | None = Field(nullable=True)
    sewa: bool | None = Field(nullable=True)
    is_lock: bool | None = Field(nullable=True)
    file_path: str | None = Field(nullable=True)
    
class PeminjamanHeaderFullBase(PeminjamanHeaderBase, BaseUUIDModel):
    pass

class PeminjamanHeader(PeminjamanHeaderFullBase, table=True):
    ptsk:"Ptsk"= Relationship(sa_relationship_kwargs = {'lazy':'select'})
    peminjaman_bidangs:list["PeminjamanBidang"] = Relationship(
        back_populates="peminjaman_header", 
        sa_relationship_kwargs = {"lazy":"select", 
                                  "primaryjoin": "PeminjamanHeader.id==PeminjamanBidang.peminjaman_header_id"})
    
    peminjaman_penggaraps:list["PeminjamanPenggarap"] = Relationship(
        sa_relationship_kwargs = {"lazy":"select",
                                  "primaryjoin": "PeminjamanHeader.id==PeminjamanPenggarap.peminjaman_header_id"})

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PeminjamanHeader.created_by_id==Worker.id",
        }
    )
    
    project: "Project" = Relationship(sa_relationship_kwargs={
        "lazy": "select"
    })

    desa: "Desa" = Relationship(sa_relationship_kwargs={
        "lazy": "select"
    })

    ptsk: "Ptsk" = Relationship(sa_relationship_kwargs={
        "lazy": "select"
    })


    @property
    def project_name(self) -> str | None:
        return self.project.name
    
    @property
    def desa_name(self) -> str | None:
        return self.desa.name
    
    @property
    def ptsk_name(self) -> str | None:
        return self.ptsk.name

    @property
    def kota_name(self) -> str | None:
        return self.desa.kota
    
    @property
    def kelurahan_name(self) -> str | None:
        return self.desa.kecamatan