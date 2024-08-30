from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from datetime import datetime, date

if TYPE_CHECKING:
    from models import (Project, Desa, Ptsk, JenisSurat, PelepasanBidang, Worker)

class PelepasanHeaderBase(SQLModel):
    nomor_pelepasan: str | None = Field(nullable=True)
    tanggal_pelepasan: date | None = Field(nullable=True)
    project_id: UUID = Field(nullable=False, foreign_key="project.id")
    desa_id: UUID = Field(nullable=False, foreign_key="desa.id")

    # IDENTITAS PEMILIK
    nama_pemilik: str | None = Field(nullable=True)
    alamat_pemilik: str | None = Field(nullable=True)
    nomor_ktp_pemilik: str | None = Field(nullable=True)
    nomor_telepon_pemilik: str | None = Field(nullable=True)

    # INFORMASI NAMA PT
    ptsk_id: UUID | None = Field(nullable=True, foreign_key="ptsk.id")
    jenis_surat_id: str | None = Field(nullable=True, foreign_key="jenis_surat_id")
    alashak: str | None = Field(nullable=True)

    # CHECKLIST KELENGKAPAN
    tanda_tangan: bool | None = Field(default=None, nullable=True)
    tanda_tangan_saksi: bool | None = Field(default=None, nullable=True)

    file_path: str | None = Field(nullable=True)
    is_lock: bool | None = Field(nullable=True, default=False)
    
class PelepasanHeaderFullBase(PelepasanHeaderBase, BaseUUIDModel):
    pass

class PelepasanHeader(PelepasanHeaderFullBase, table=True):
    
    project: "Project" = Relationship(sa_relationship_kwargs={
        "lazy": "select"
    })

    desa: "Desa" = Relationship(sa_relationship_kwargs={
        "lazy": "select"
    })

    ptsk: "Ptsk" = Relationship(sa_relationship_kwargs={
        "lazy": "select"
    })

    jenis_surat: "JenisSurat" = Relationship(sa_relationship_kwargs={
        "lazy": "select"
    })

    pelepasan_bidangs: list["PelepasanBidang"] = Relationship(sa_relationship_kwargs={
        "lazy": "select",
        "primaryjoin": "PelepasanHeader.id==PelepasanBidang.pelepasan_header_id",
    })

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PelepasanHeader.created_by_id==Worker.id",
        }
    )

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
    def jenis_surat_name(self) -> str | None:
        return self.jenis_surat.name




    