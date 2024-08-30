from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import (KategoriTipeTanahEnum)
from datetime import date

if TYPE_CHECKING:
    from models import (Planing, Ptsk, PeminjamanBidang, PeminjamanPenggarap)

class PeminjamanHeaderBase(SQLModel):
    nomor_perjanjian: str | None = Field(nullable=False)
    tanggal_perjanjian: date | None = Field(nullable=True)
    tanggal_berahkir: date | None = Field(nullable=True)
    planing_id: UUID | None = Field(nullable=True, foreign_key="planing.id")
    ptsk_id: UUID | None = Field(nullable=True, foreign_key="ptsk.id")
    kategori: KategoriTipeTanahEnum | None = Field(nullable=True)
    tanda_tangan_lurah: bool | None = Field(nullable=True)
    produktivitas_tanah: bool | None = Field(nullable=True)
    gratis: bool | None = Field(nullable=True)
    sewa: bool | None = Field(nullable=True)
    file_path: str | None = Field(nullable=True)
    
class PeminjamanHeaderFullBase(PeminjamanHeaderBase, BaseUUIDModel):
    pass

class PeminjamanHeader(PeminjamanHeaderFullBase, table=True):
    planing:"Planing" = Relationship(sa_relationship_kwargs = {'lazy':'select'})
    ptsk:"Ptsk"= Relationship(sa_relationship_kwargs = {'lazy':'select'})
    peminjaman_bidangs:list["PeminjamanBidang"] = Relationship(back_populates="peminjaman_header", sa_relationship_kwargs = {'lazy':'select'})
    peminjaman_penggaraps:list["PeminjamanPenggarap"] = Relationship(sa_relationship_kwargs = {'lazy':'select'})

    @property
    def project_name(self) -> str:
        if self.planing is None:
            return ""
        
        return self.planing.project.name
    
    @property
    def desa_name(self)-> str:
        if self.desa_name is None:
            return ""
        return self.planing.desa.name
