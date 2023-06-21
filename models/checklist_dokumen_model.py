from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum

if TYPE_CHECKING:
    from models.dokumen_model import Dokumen

class ChecklistDokumenBase(SQLModel):
    jenis_alashak:JenisAlashakEnum
    kategori_penjual:KategoriPenjualEnum
    jenis_bayar:JenisBayarEnum
    dokumen_id:UUID = Field(default=None, foreign_key="dokumen.id")

class ChecklistDokumenFullBase(BaseUUIDModel, ChecklistDokumenBase):
    pass

class ChecklistDokumen(ChecklistDokumenFullBase, table=True):

    dokumen:"Dokumen" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def dokumen_name(self) -> str:
        return self.dokumen.name or ""
    