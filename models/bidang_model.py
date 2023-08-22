from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import MappingBidangOverlap
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID
from decimal import Decimal
from common.enum import (JenisBidangEnum, StatusBidangEnum, JenisAlashakEnum, StatusSKEnum,
                         StatusBidangEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum)

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.skpt_model import Skpt
    from models.ptsk_model import Ptsk
    from models.pemilik_model import Pemilik
    from models.master_model import JenisSurat
    from models.kategori_model import Kategori, KategoriSub, KategoriProyek
    from models.marketing_model import Manager, Sales
    from models.notaris_model import Notaris
    from models.bundle_model import BundleHd
    from models.hasil_peta_lokasi_model import HasilPetaLokasi
    from models.worker_model import Worker
    
class BidangBase(SQLModel):
    id_bidang:Optional[str] = Field(nullable=False, max_length=150)
    id_bidang_lama:Optional[str] = Field(nullable=True)
    no_peta:Optional[str] = Field(nullable=True)
    pemilik_id:Optional[UUID] = Field(nullable=True, foreign_key="pemilik.id")
    jenis_bidang:JenisBidangEnum | None = Field(nullable=True)
    status:StatusBidangEnum | None = Field(nullable=False)
    planing_id:Optional[UUID] = Field(nullable=True, foreign_key="planing.id")
    group:Optional[str] = Field(nullable=True)
    jenis_alashak:Optional[JenisAlashakEnum] = Field(nullable=True)
    jenis_surat_id:Optional[UUID] = Field(nullable=True, foreign_key="jenis_surat.id")
    alashak:Optional[str] = Field(nullable=True)
    kategori_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori.id")
    kategori_sub_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori_sub.id")
    kategori_proyek_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori_proyek.id")
    skpt_id:Optional[UUID] = Field(nullable=True, foreign_key="skpt.id") #PT SK
    penampung_id:Optional[UUID] = Field(nullable=True, foreign_key="ptsk.id") #PT Penampung
    manager_id:Optional[UUID] = Field(nullable=True, foreign_key="manager.id")
    sales_id:Optional[UUID] = Field(nullable=True, foreign_key="sales.id")
    mediator:Optional[str] = Field(nullable=True)
    telepon_mediator:Optional[str] = Field(nullable=True)
    notaris_id:Optional[UUID] = Field(nullable=True, foreign_key="notaris.id")
    tahap:Optional[str] = Field(nullable=True)
    informasi_tambahan:Optional[str] = Field(nullable=True)
    luas_surat:Optional[Decimal] = Field(nullable=True)
    luas_ukur:Optional[Decimal] = Field(nullable=True)
    luas_gu_perorangan:Optional[Decimal] = Field(nullable=True)
    luas_gu_pt:Optional[Decimal] = Field(nullable=True)
    luas_nett:Optional[Decimal] = Field(nullable=True)
    luas_clear:Optional[Decimal] = Field(nullable=True)
    luas_pbt_perorangan:Optional[Decimal] = Field(nullable=True)
    luas_pbt_pt:Optional[Decimal] = Field(nullable=True)

    bundle_hd_id:UUID | None = Field(nullable=True, foreign_key="bundle_hd.id")

class BidangRawBase(BaseUUIDModel, BidangBase):
    pass

class BidangFullBase(BaseGeoModel, BidangRawBase):
    pass

class Bidang(BidangFullBase, table=True):
    pemilik:"Pemilik" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    planing:"Planing" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    jenis_surat:"JenisSurat" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    kategori:"Kategori" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin' })
    
    kategori_sub:"KategoriSub" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    kategori_proyek:"KategoriProyek" = Relationship(
        sa_relationship_kwargs = {'lazy':'selectin'})
    
    skpt:"Skpt" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    penampung:"Ptsk" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    manager:"Manager" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    sales:"Sales" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    notaris:"Notaris" = Relationship(
        sa_relationship_kwargs={'lazy':'selectin'})
    
    bundlehd:"BundleHd" = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs={'lazy':'selectin'})
    
    hasil_peta_lokasi:"HasilPetaLokasi" = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs=
        {
            "lazy":"selectin",
            "uselist":False
        }
    )
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Bidang.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def pemilik_name(self) -> str:
        if self.pemilik is None:
            return ""
        
        return self.pemilik.name
    
    @property
    def project_name(self) -> str:
        if self.planing is None:
            return ""
        
        return self.planing.project.name
    
    @property
    def desa_name(self) -> str:
        if self.planing is None:
            return ""
        
        return self.planing.desa.name
    
    @property
    def desa_code(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), 'code', None)
    
    @property
    def planing_name(self) -> str:
        if self.planing is None:
            return ""
        
        return self.planing.name
    
    @property
    def jenis_surat_name(self) -> str:
        if self.jenis_surat is None:
            return ""
        
        return self.jenis_surat.name
    
    @property
    def kategori_name(self) -> str:
        if self.kategori is None:
            return ""
        
        return self.kategori.name
    
    @property
    def kategori_sub_name(self) -> str:
        if self.kategori_sub is None:
            return ""
        
        return self.kategori_sub.name
    
    @property
    def kategori_proyek_name(self) -> str:
        if self.kategori_proyek is None:
            return ""
        
        return self.kategori_proyek.name
    
    @property
    def ptsk_name(self) -> str:
        if self.skpt is None:
            return ""
        # return getattr(getattr(getattr(self, 'skpt'), 'ptsk'), 'name')
        return self.skpt.ptsk.name
    
    @property
    def no_sk(self) -> str:
        if self.skpt is None:
            return ""
        
        return self.skpt.nomor_sk
    
    @property
    def status_sk(self) -> str:
        if self.skpt is None:
            return ""
        
        return self.skpt.status
    
    @property
    def penampung_name(self) -> str:
        if self.penampung is None:
            return ""
        
        return self.penampung.name
    
    @property
    def manager_name(self) -> str:
        if self.manager is None:
            return ""
        
        return self.manager.name
    
    @property
    def sales_name(self) -> str:
        if self.sales is None:
            return ""
        
        return self.sales.name
    
    @property
    def notaris_name(self) -> str:
        if self.notaris is None:
            return ""
        
        return self.notaris.name
    
    @property
    def hasil_analisa_peta_lokasi(self) -> HasilAnalisaPetaLokasiEnum | None:
        return getattr(getattr(self, "hasil_peta_lokasi", None), "hasil_analisa_peta_lokasi", None)
    
    @property
    def proses_bpn_order_gu(self) -> ProsesBPNOrderGambarUkurEnum | None:
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Belum_IL and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap:
            return ProsesBPNOrderGambarUkurEnum.PBT_Perorangan
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Belum_IL and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear:
            return ProsesBPNOrderGambarUkurEnum.PBT_Perorangan
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Sudah_Il and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap:
            return ProsesBPNOrderGambarUkurEnum.PBT_Perorangan
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Sudah_Il and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear:
            return ProsesBPNOrderGambarUkurEnum.PBT_PT
        
        return None


