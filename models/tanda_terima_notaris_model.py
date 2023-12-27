from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from common.enum import JenisAlashakEnum, KategoriPenjualEnum, StatusPetaLokasiEnum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.kjb_model import KjbHd, KjbDt
    from models.master_model import JenisSurat
    from models.notaris_model import Notaris
    from models.desa_model import Desa
    from models.project_model import Project
    from models.dokumen_model import Dokumen
    from models.pemilik_model import Pemilik
    from models.worker_model import Worker

class TandaTerimaNotarisHdBase(SQLModel):
    # kjb_hd_id:UUID = Field(nullable=False, foreign_key="kjb_hd.id")
    kjb_dt_id:UUID = Field(nullable=False, foreign_key="kjb_dt.id")
    tanggal_tanda_terima:date | None = Field(default=date.today())
    nomor_tanda_terima:str
    notaris_id:UUID = Field(nullable=False, foreign_key="notaris.id")
    desa_id:UUID | None = Field(nullable=True, foreign_key="desa.id")
    project_id:UUID | None = Field(nullable=True, foreign_key="project.id")
    luas_surat:Decimal
    pemilik_id:UUID | None = Field(foreign_key="pemilik.id", nullable=True)
    status_peta_lokasi:StatusPetaLokasiEnum | None = Field(nullable=True)
    file_path:str | None = Field(nullable=True)
    group:str | None = Field(nullable=True)


class TandaTerimaNotarisHdFullBase(BaseUUIDModel, TandaTerimaNotarisHdBase):
    pass

class TandaTerimaNotarisHd(TandaTerimaNotarisHdFullBase, table=True):
    # kjb_hd:"KjbHd" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})
    kjb_dt:"KjbDt" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'select'})
    notaris:"Notaris" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    desa:"Desa" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    project:"Project" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    pemilik:"Pemilik" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    tanda_terima_notaris_dts:list["TandaTerimaNotarisDt"] = Relationship(sa_relationship_kwargs={'lazy':'select'})
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "TandaTerimaNotarisHd.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def alashak(self) -> str:
        return self.kjb_dt.alashak
    
    @property
    def jenis_surat_name(self) -> str:
        return self.kjb_dt.jenis_surat.name
    
    @property
    def notaris_name(self) -> str:
        return self.notaris.name
    
    @property
    def desa_name(self) -> str:
        if self.desa is None:
            return ""
        return self.desa.name
    
    @property
    def project_name(self) -> str:
        if self.project is None:
            return ""
        return self.project.name
    
    @property
    def done_request_petlok(self) -> bool:
        status = False

        if self.kjb_dt.request_peta_lokasi:
            status = True
        
        return status
    
    @property
    def nomor_telepon(self) -> list[str] | None:
        kontaks = []
        if self.pemilik is None:
            return kontaks
        for i in self.pemilik.kontaks:
            kontaks.append(i.nomor_telepon)
        
        return kontaks
    
    @property
    def pemilik_name(self) -> str | None:
        if self.pemilik is None:
            return ""
        return self.pemilik.name



class TandaTerimaNotarisDtBase(SQLModel):
    tanggal_tanda_terima:date | None = Field(default=date.today())
    dokumen_id:UUID = Field(foreign_key="dokumen.id")
    meta_data:str | None
    history_data:str | None
    riwayat_data:str | None
    tanggal_terima_dokumen:date | None = Field(default=date.today())
    file_path:str | None = Field(nullable=True)
    tanda_terima_notaris_hd_id:UUID = Field(foreign_key="tanda_terima_notaris_hd.id", nullable=False)
    
class TandaTerimaNotarisDtFullBase(BaseUUIDModel, TandaTerimaNotarisDtBase):
    pass

class TandaTerimaNotarisDt(TandaTerimaNotarisDtFullBase, table=True):
    dokumen:"Dokumen" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    tanda_terima_notaris_hd:"TandaTerimaNotarisHd" = Relationship(back_populates="tanda_terima_notaris_dts", sa_relationship_kwargs={'lazy':'select'})
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "TandaTerimaNotarisDt.updated_by_id==Worker.id",
        }
    )

    class Meta:
        order_fields = {
            # 'all' : True,
            # 'all_join': False,
            'dokumen_name' : 'dokumen.name',
            'updated_by_name' : 'worker_1.name'
        }


    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def dokumen_name(self) -> str:
        return self.dokumen.name
    
    @property
    def nomor_tanda_terima(self) -> str:
        return self.tanda_terima_notaris_hd.nomor_tanda_terima
    
    @property
    def kategori_dokumen_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'dokumen', None), 'kategori_dokumen', None), 'name', None)


