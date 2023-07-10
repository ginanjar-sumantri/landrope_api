from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID

if TYPE_CHECKING:
    from kjb_model import KjbDt

class RequestPetaLokasiBase(SQLModel):
    code:str = Field(nullable=True)
    tanggal:datetime = Field(default=datetime.now(), nullable=False)
    remark:str
    dibuat_oleh:str | None = Field(default_factory="Land Adm Acquisition Officer")
    diperiksa_oleh:str | None = Field(default_factory="Land Adm & Verification Section Head")
    diterima_oleh:str | None = Field(default_factory="Land Measurement Analyst")
    is_disabled:bool | None = Field(nullable=True, default_factory=False)

    kjb_dt_id:UUID = Field(foreign_key="kjb_dt.id", nullable=False)

class RequestPetaLokasiFullBase(BaseUUIDModel, RequestPetaLokasiBase):
    pass

class RequestPetaLokasi(RequestPetaLokasiFullBase, table=True):
    kjb_dt: "KjbDt" = Relationship(back_populates="request_peta_lokasi", sa_relationship_kwargs={'lazy':'selectin'})

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
    def nama_pemilik_tanah(self) -> str:
        return self.kjb_dt.pemilik.name
    
    @property
    def nomor_pemilik_tanah(self) -> str:
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
    def desa_name(self) -> str:
        return self.kjb_dt.desa.name
    
    @property
    def project_name(self) -> str:
        return self.kjb_dt.project.name
    
