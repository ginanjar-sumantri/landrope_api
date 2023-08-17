# from sqlmodel import SQLModel, Field, Relationship
# from models.base_model import BaseUUIDModel
# from uuid import UUID
# from typing import TYPE_CHECKING
# from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum

# if TYPE_CHECKING:
#     from models.dokumen_model import Dokumen
#     from models.worker_model import Worker
#     from models.bidang_model import Bidang

# class ChecklistKelengkapanDokumenBase(SQLModel):
#     bidang_id:UUID = Field(nullable=False, foreign_key="bidang.id")
#     jenis_bayar:JenisBayarEnum
#     dokumen_id:UUID = Field(default=None, foreign_key="dokumen.id")

# class ChecklistKelengkapanDokumenFullBase(BaseUUIDModel, ChecklistKelengkapanDokumenBase):
#     pass

# class ChecklistKelengkapanDokumen(ChecklistKelengkapanDokumenFullBase, table=True):
#     bidang:"Bidang" = Relationship(
#         sa_relationship_kwargs=
#         {
#             'lazy' : 'selectin'
#         })
    
#     dokumen:"Dokumen" = Relationship(
#         sa_relationship_kwargs=
#         {
#             'lazy':'selectin'
#         })
#     worker: "Worker" = Relationship(  
#         sa_relationship_kwargs=
#         {
#             "lazy": "joined",
#             "primaryjoin": "ChecklistDokumen.updated_by_id==Worker.id",
#         })
    
#     @property
#     def updated_by_name(self) -> str | None:
#         return getattr(getattr(self, 'worker', None), 'name', None)

#     @property
#     def dokumen_name(self) -> str:
#         return self.dokumen.name or ""
    
#     @property
#     def kategori_dokumen_name(self) -> str | None:
#         return getattr(getattr(getattr(self, 'dokumen', None), 'kategori_dokumen', None), 'name', None)