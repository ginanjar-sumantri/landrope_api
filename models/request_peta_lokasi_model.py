from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from datetime import datetime, date
from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID
from common.enum import JenisAlashakEnum, HasilAnalisaPetaLokasiEnum

if TYPE_CHECKING:
    from kjb_model import KjbDt
    from worker_model import Worker
    from hasil_peta_lokasi_model import HasilPetaLokasi

class RequestPetaLokasiBase(SQLModel):
    code:str = Field(nullable=True)
    tanggal:date = Field(default=date.today(), nullable=False)
    remark:str
    is_disabled:bool | None = Field(nullable=True)

    kjb_dt_id:UUID = Field(foreign_key="kjb_dt.id", nullable=False)

class RequestPetaLokasiFullBase(BaseUUIDModel, RequestPetaLokasiBase):
    pass

class RequestPetaLokasi(RequestPetaLokasiFullBase, table=True):
    kjb_dt: "KjbDt" = Relationship(back_populates="request_peta_lokasi", sa_relationship_kwargs={'lazy':'select'})
    hasil_peta_lokasi: "HasilPetaLokasi" = Relationship(
        back_populates="request_peta_lokasi",
        sa_relationship_kwargs={
            "lazy" : "select",
            "uselist" : False
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "RequestPetaLokasi.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def alashak(self) -> str | None:
        return self.kjb_dt.alashak
    
    @property
    def kjb_hd_code(self) -> str:
        return self.kjb_dt.kjb_hd.code

    @property
    def mediator(self) -> str:
        return self.kjb_dt.kjb_hd.mediator
    
    @property
    def group(self) -> str:
        return self.kjb_dt.kjb_hd.nama_group
    
    @property
    def nama_pemilik_tanah(self) -> str | None:
        return getattr(getattr(getattr(self, 'kjb_dt', None), 'pemilik', None), 'name', None)
    
    @property
    def nomor_pemilik_tanah(self) -> str:
        if self.kjb_dt.pemilik is None:
            return ""
        
        nomors = [i.nomor_telepon for i in self.kjb_dt.pemilik.kontaks]

        if len(nomors) == 0:
            return ""
        elif len(nomors) == 1:
            return nomors[0]
        else:
            return ",".join(nomors)
        
    @property
    def luas(self) -> Decimal:
        return self.kjb_dt.luas_surat_by_ttn
    
    @property
    def desa_name(self) -> str | None:
        if self.kjb_dt.desa_by_ttn is None:
            return ""
        return self.kjb_dt.desa_by_ttn.name
    
    @property
    def desa_hd_name(self) -> str | None:
        if self.kjb_dt.kjb_hd.desa is None:
            return "" 
        return self.kjb_dt.kjb_hd.desa.name
    
    @property
    def project_name(self) -> str:
        if self.kjb_dt.project_by_ttn is None:
            return ""
        return self.kjb_dt.project_by_ttn.name
    
    @property
    def jenis_alashak_kjb_dt(self) -> str | None:
        return getattr(getattr(self, "kjb_dt", None), "jenis_alashak", None)
    
    @property
    def id_bidang_hasil_peta_lokasi(self) -> str | None:
        return getattr(getattr(getattr(self, "hasil_peta_lokasi", None), "bidang", None), "id_bidang", None)
    
    @property
    def hasil_peta_lokasi_id(self) -> UUID | None:
        return getattr(getattr(self, "hasil_peta_lokasi", None), "id", None)
    
