from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseHistoryModel
from common.enum import JenisAlashakEnum
from typing import TYPE_CHECKING
from uuid import UUID
from decimal import Decimal
from common.enum import TipeOverlapEnum, StatusHasilPetaLokasiEnum, HasilAnalisaPetaLokasiEnum, StatusLuasOverlapEnum

if TYPE_CHECKING:
    from models import Bidang, KjbDt, Planing, RequestPetaLokasi, Skpt, Pemilik, Worker, BidangOverlap, SubProject

class HasilPetaLokasiBase(SQLModel):
    bidang_id:UUID | None = Field(nullable=True, foreign_key="bidang.id")
    kjb_dt_id:UUID = Field(nullable=False, foreign_key="kjb_dt.id")
    request_peta_lokasi_id:UUID = Field(nullable=False, foreign_key="request_peta_lokasi.id")
    planing_id:UUID = Field(nullable=False, foreign_key="planing.id")
    sub_project_id:UUID | None = Field(nullable=True, foreign_key="sub_project.id")
    skpt_id:UUID = Field(nullable=False, foreign_key="skpt.id")
    no_peta:str = Field(nullable=False)
    pemilik_id:UUID = Field(nullable=False, foreign_key="pemilik.id")
    jenis_alashak:JenisAlashakEnum | None
    alashak:str = Field(nullable=False)
    luas_surat:Decimal = Field(nullable=False)
    luas_ukur:Decimal = Field(nullable=False)
    luas_nett:Decimal | None = Field(nullable=True)
    luas_clear:Decimal = Field(nullable=True)
    luas_gu_perorangan:Decimal | None = Field(nullable=True)
    luas_gu_pt:Decimal | None = Field(nullable=True)
    file_path:str | None = Field(nullable=True)
    status_hasil_peta_lokasi:StatusHasilPetaLokasiEnum = Field(nullable=False)
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None = Field(nullable=True)
    remark:str | None = Field(nullable=True)
    is_done:bool | None = Field(nullable=True, default=False)

class HasilPetaLokasiFullBase(BaseUUIDModel, HasilPetaLokasiBase):
    pass

class HasilPetaLokasi(HasilPetaLokasiFullBase, table=True):
    details: list["HasilPetaLokasiDetail"] = Relationship(
                        back_populates="hasil_peta_lokasi",
                        sa_relationship_kwargs=
                        {
                            "lazy" : "select"
                        }
    )

    hasil_peta_lokasi_histories: list["HasilPetaLokasiHistory"] = Relationship(
        back_populates="hasil_peta_lokasi",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    bidang: "Bidang" = Relationship(
                        back_populates="hasil_peta_lokasi",
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "select"
                                            })
    
    kjb_dt: "KjbDt" = Relationship(
                        back_populates="hasil_peta_lokasi",
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "select"
                                            }
                        )
    
    request_peta_lokasi: "RequestPetaLokasi" = Relationship(
                        back_populates="hasil_peta_lokasi",
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "select"
                                            })
    
    planing: "Planing" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "select"
                                            })
    sub_project: "SubProject" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "select"
                                            })

    skpt: "Skpt" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "select"
                                            })
    
    pemilik: "Pemilik" = Relationship(
                        sa_relationship_kwargs=
                                            {
                                                "lazy" : "select"
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
    def sub_project_name(self) -> str | None:
        return getattr(getattr(self, 'sub_project', None), 'name', None)
    
    @property
    def sub_project_exists(self) -> bool | None:
        return getattr(getattr(getattr(self, 'planing', False), 'project', False), 'sub_project_exists', False)
    
    @property
    def project_id(self) -> UUID | None:
        return getattr(getattr(self, 'planing', None), 'project_id', None)
    
    @property
    def project_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'project', None), 'name', None)
    
    @property
    def desa_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), 'name', None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'skpt', None), 'ptsk', None), 'name', None)
    
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
    hasil_peta_lokasi_id:UUID | None = Field(nullable=False, foreign_key="hasil_peta_lokasi.id")
    luas_overlap:Decimal = Field(nullable=True)
    keterangan:str | None = Field(nullable=True)
    status_luas:StatusLuasOverlapEnum | None = Field(nullable=True)
    bidang_overlap_id:UUID | None = Field(nullable=True, foreign_key="bidang_overlap.id")

class HasilPetaLokasiDetailFullBase(BaseUUIDModel, HasilPetaLokasiDetailBase):
    pass

class HasilPetaLokasiDetail(HasilPetaLokasiDetailFullBase, table=True):
    hasil_peta_lokasi : "HasilPetaLokasi" = Relationship(
                            back_populates="details",
                            sa_relationship_kwargs=
                            {
                                "lazy" : "select"
                            }
    )

    bidang : "Bidang" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "select"
                            }
    )

    bidang_overlap : "BidangOverlap" = Relationship(
                            back_populates="hasil_peta_lokasi_detail",
                            sa_relationship_kwargs=
                            {
                                "lazy" : "select"
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


##########################################################

class HasilPetaLokasiHistoryBase(SQLModel):
    hasil_peta_lokasi_id:UUID = Field(foreign_key="hasil_peta_lokasi.id", nullable=False)

class HasilPetaLokasiHistoryBaseExt(HasilPetaLokasiHistoryBase, BaseHistoryModel):
    pass

class HasilPetaLokasiHistoryFullBase(BaseUUIDModel, HasilPetaLokasiHistoryBaseExt):
    pass

class HasilPetaLokasiHistory(HasilPetaLokasiHistoryFullBase, table=True):
    hasil_peta_lokasi:"HasilPetaLokasi" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        },
        back_populates="hasil_peta_lokasi_histories"
    )

    trans_worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "HasilPetaLokasiHistory.trans_worker_id==Worker.id",
        }
    )

    @property
    def trans_worker_name(self) -> str | None:
        return getattr(getattr(self, "trans_worker", None), "name", None)