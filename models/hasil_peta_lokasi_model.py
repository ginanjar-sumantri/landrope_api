from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import JenisAlashakEnum
from typing import TYPE_CHECKING
from uuid import UUID
from decimal import Decimal
from common.enum import TipeOverlapEnum, StatusHasilPetaLokasiEnum

if TYPE_CHECKING:
    from models.bidang_model import Bidang
    from models.kjb_model import KjbDt
    from models.request_peta_lokasi_model import RequestPetaLokasi
    from models.planing_model import Planing
    from models.ptsk_model import Ptsk
    from models.skpt_model import Skpt
    from models.pemilik_model import Pemilik
    from models.worker_model import Worker
    from models.bidang_overlap_model import BidangOverlap

class HasilPetaLokasiBase(SQLModel):
    bidang_id:UUID | None = Field(nullable=True, foreign_key="bidang.id")
    kjb_dt_id:UUID = Field(nullable=False, foreign_key="kjb_dt.id")
    request_peta_lokasi_id:UUID = Field(nullable=False, foreign_key="request_peta_lokasi.id")
    planing_id:UUID = Field(nullable=False, foreign_key="planing.id")
    ptsk_id:UUID = Field(nullable=False, foreign_key="ptsk.id")
    skpt_id:UUID = Field(nullable=False, foreign_key="skpt.id")
    no_peta:str = Field(nullable=False)
    pemilik_id:UUID = Field(nullable=False, foreign_key="pemilik.id")
    jenis_alashak:JenisAlashakEnum | None
    alashak:str = Field(nullable=False)
    luas_surat:Decimal = Field(nullable=False)
    luas_ukur:Decimal = Field(nullable=False)
    luas_gu_perorangan:Decimal | None = Field(nullable=True)
    luas_gu_pt:Decimal | None = Field(nullable=True)
    file_path:str | None = Field(nullable=True)
    status_hasil_peta_lokasi:StatusHasilPetaLokasiEnum = Field(nullable=False)

class HasilPetaLokasiFullBase(BaseUUIDModel, HasilPetaLokasiBase):
    pass

class HasilPetaLokasi(HasilPetaLokasiFullBase, table=True):
    details: "HasilPetaLokasiDetail" = Relationship(
                        back_populates="hasil_peta_lokasi",
                        sa_relationship_kwargs=
                        {
                            "lazy" : "selectin"
                        }
    )

    bidang: "Bidang" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "selectin"
                                            })
    
    kjb_dt: "KjbDt" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "selectin"
                                            })
    
    request_peta_lokasi: "RequestPetaLokasi" = Relationship(
                        back_populates="hasil_peta_lokasi",
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "selectin"
                                            })
    
    planing: "Planing" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "selectin"
                                            })
    
    ptsk: "Ptsk" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "selectin"
                                            })
    
    skpt: "Skpt" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "selectin"
                                            })
    
    pemilik: "Pemilik" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "selectin"
                                            })
    
    worker: "Worker" = Relationship(  
                        sa_relationship_kwargs=
                                            {
                                                "lazy": "joined",
                                                "primaryjoin": "HasilPetaLokasi.updated_by_id==Worker.id",
                                            })
    
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(self, 'bidang', None), 'id_bidang', None)
    
    @property
    def alashak_bidang(self) -> str | None:
        return getattr(getattr(self, 'bidang', None), 'alashak', None)
    
    @property
    def alashak_kjb_dt(self) -> str | None:
        return getattr(getattr(self, 'kjb_dt', None), 'alashak', None)
    
    @property
    def planing_name(self) -> str | None:
        return getattr(getattr(self, 'planing', None), 'name', None)
    
    @property
    def project_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'project', None), 'name', None)
    
    @property
    def desa_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), 'name', None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, 'ptsk', None), 'name', None)
    
    @property
    def no_sk(self) -> str | None:
        return getattr(getattr(self, 'skpt', None), 'nomor_sk', None)
    
    @property
    def status_sk(self) -> str | None:
        return getattr(getattr(self, 'skpt', None), 'status', None)
    
    @property
    def pemilik_name(self) -> str | None:
        return getattr(getattr(self, 'pemilik', None), 'name', None)
    
    ##########################################################

class HasilPetaLokasiDetailBase(SQLModel):
    tipe_overlap:TipeOverlapEnum
    bidang_id:UUID | None = Field(nullable=True, foreign_key="bidang.id")
    hasil_peta_lokasi_id:UUID = Field(nullable=False, foreign_key="hasil_peta_lokasi.id")
    luas_overlap:Decimal = Field(nullable=True)
    keterangan:str | None = Field(nullable=True)
    bidang_overlap_id:UUID | None = Field(nullable=True, foreign_key="bidang_overlap.id")

class HasilPetaLokasiDetailFullBase(BaseUUIDModel, HasilPetaLokasiDetailBase):
    pass

class HasilPetaLokasiDetail(HasilPetaLokasiDetailFullBase, table=True):
    hasil_peta_lokasi : "HasilPetaLokasi" = Relationship(
                            back_populates="details",
                            sa_relationship_kwargs=
                            {
                                "lazy" : "selectin"
                            }
    )

    bidang : "Bidang" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "selectin"
                            }
    )

    bidang_overlap : "BidangOverlap" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "selectin"
                            }
    )

    @property
    def id_bidang(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def luas_surat(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "luas_surat", None)
    
    @property
    def alashak(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def pemilik_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'bidang', None), 'pemilik', None), 'name', None)