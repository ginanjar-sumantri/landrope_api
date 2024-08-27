from sqlmodel import SQLModel, Field, Relationship, Column
from models.base_model import BaseUUIDModel, BaseGeoModel, BaseHistoryModel
from sqlalchemy import Column, String
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import condecimal
from common.enum import (JenisBidangEnum, StatusBidangEnum, JenisAlashakEnum, StatusSKEnum,
                         StatusBidangEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum,
                         SatuanBayarEnum, SatuanHargaEnum, JenisBayarEnum, StatusPembebasanEnum, KategoriLahanEnum)
from geoalchemy2 import Geometry
import json
from datetime import datetime

if TYPE_CHECKING:
    from models import (Planing, SubProject, Skpt, Ptsk, Pemilik, JenisSurat, Kategori, KategoriSub, KategoriProyek, Manager, Sales,
                        Notaris, BundleHd, HasilPetaLokasi, Worker, BidangKomponenBiaya, BidangOverlap, Invoice, TahapDetail, PeminjamanBidang)
    
class BidangBase(SQLModel):
    id_bidang:Optional[str] = Field(nullable=False, max_length=150, sa_column=(Column("id_bidang", String, unique=True)))
    id_bidang_lama:Optional[str] = Field(nullable=True, sa_column=(Column("id_bidang_lama", String, unique=True)))
    no_peta:Optional[str] = Field(nullable=True)
    pemilik_id:Optional[UUID] = Field(nullable=True, foreign_key="pemilik.id")
    jenis_bidang:JenisBidangEnum | None = Field(nullable=True)
    status:StatusBidangEnum | None = Field(nullable=False)
    planing_id:Optional[UUID] = Field(nullable=True, foreign_key="planing.id")
    sub_project_id:Optional[UUID] = Field(nullable=True, foreign_key="sub_project.id")
    group:Optional[str] = Field(nullable=True)
    jenis_alashak:Optional[JenisAlashakEnum] = Field(nullable=True)
    jenis_surat_id:Optional[UUID] = Field(nullable=True, foreign_key="jenis_surat.id")
    alashak:Optional[str] = Field(nullable=True)
    kategori_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori.id")
    kategori_sub_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori_sub.id")
    kategori_proyek_id:Optional[UUID] = Field(nullable=True, foreign_key="kategori_proyek.id")
    kategori_lahan: KategoriLahanEnum | None = Field(nullable=True, default=KategoriLahanEnum.DARAT)
    skpt_id:Optional[UUID] = Field(nullable=True, foreign_key="skpt.id") #PT SK
    penampung_id:Optional[UUID] = Field(nullable=True, foreign_key="ptsk.id") #PT Penampung
    manager_id:Optional[UUID] = Field(nullable=True, foreign_key="manager.id")
    sales_id:Optional[UUID] = Field(nullable=True, foreign_key="sales.id")
    mediator:Optional[str] = Field(nullable=True)
    telepon_mediator:Optional[str] = Field(nullable=True)
    notaris_id:Optional[UUID] = Field(nullable=True, foreign_key="notaris.id")
    tahap:Optional[int] = Field(nullable=True)
    informasi_tambahan:Optional[str] = Field(nullable=True)
    luas_surat:Optional[Decimal] = Field(nullable=True)
    luas_ukur:Optional[Decimal] = Field(nullable=True)
    luas_gu_perorangan:Optional[Decimal] = Field(nullable=True)
    luas_gu_pt:Optional[Decimal] = Field(nullable=True)
    luas_nett:Optional[Decimal] = Field(nullable=True)
    luas_clear:Optional[Decimal] = Field(nullable=True)
    luas_pbt_perorangan:Optional[Decimal] = Field(nullable=True)
    luas_pbt_pt:Optional[Decimal] = Field(nullable=True)
    luas_bayar:Optional[Decimal] = Field(nullable=True)
    luas_proses:Optional[Decimal] = Field(nullable=True)
    luas_produk:Optional[Decimal] = Field(nullable=True)
    harga_akta:Optional[Decimal] = Field(nullable=True)
    harga_transaksi:Optional[Decimal] = Field(nullable=True)
    # harga_ptsl: Decimal | None = Field(nullable=True)

    bundle_hd_id:UUID | None = Field(nullable=True, foreign_key="bundle_hd.id")
    njop:Decimal|None = Field(nullable=True)
    status_pembebasan:StatusPembebasanEnum|None = Field(nullable=True)
    parent_id:UUID|None = Field(nullable=True, foreign_key="bidang.id")
    # is_ptsl: bool | None = Field(nullable=True, default=False)
    
class BidangRawBase(BaseUUIDModel, BidangBase):
    pass

class BidangFullBase(BaseGeoModel, BidangRawBase):
    geom_ori:str | None = Field(sa_column=Column(Geometry), nullable=True)

class Bidang(BidangFullBase, table=True):
    bidang_histories: "BidangHistory" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        },
        back_populates="bidang"
    )

    parent_bintang: "Bidang" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "select",
            "primaryjoin": "Bidang.parent_id==Bidang.id",
        }
    )

    pemilik:"Pemilik" = Relationship(
        sa_relationship_kwargs = {'lazy':'select'})
    
    planing:"Planing" = Relationship(
        sa_relationship_kwargs = {'lazy':'select'})
    
    sub_project:"SubProject" = Relationship(
        sa_relationship_kwargs=
        {
            'lazy' : 'select'
        }
    )
    
    jenis_surat:"JenisSurat" = Relationship(
        sa_relationship_kwargs = {'lazy':'select'})
    
    kategori:"Kategori" = Relationship(
        sa_relationship_kwargs = {'lazy':'select' })
    
    kategori_sub:"KategoriSub" = Relationship(
        sa_relationship_kwargs = {'lazy':'select'})
    
    kategori_proyek:"KategoriProyek" = Relationship(
        sa_relationship_kwargs = {'lazy':'select'})
    
    skpt:"Skpt" = Relationship(
        sa_relationship_kwargs={'lazy':'select'})
    
    penampung:"Ptsk" = Relationship(
        sa_relationship_kwargs={'lazy':'select'})
    
    manager:"Manager" = Relationship(
        sa_relationship_kwargs={'lazy':'select'})
    
    sales:"Sales" = Relationship(
        sa_relationship_kwargs={'lazy':'select'})
    
    notaris:"Notaris" = Relationship(
        sa_relationship_kwargs={'lazy':'select'})
    
    bundlehd:"BundleHd" = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs={'lazy':'select'})
    
    hasil_peta_lokasi:"HasilPetaLokasi" = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs=
        {
            "lazy":"select",
            "uselist":False
        }
    )

    komponen_biayas:list["BidangKomponenBiaya"] = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )

    overlaps:list["BidangOverlap"] = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs=
        {
            "lazy":"select",
            "primaryjoin": "Bidang.id==BidangOverlap.parent_bidang_id"
        }
    )

    invoices:list["Invoice"] = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )

    tahap_details:list["TahapDetail"] = Relationship(
        back_populates="bidang",
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Bidang.created_by_id==Worker.id",
        }
    )

    worker_update: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Bidang.updated_by_id==Worker.id",
        }
    )

    peminjaman_bidang: "PeminjamanBidang" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})


    @property
    def created_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker_update', None), 'name', None)
    
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
    def kota(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), 'kota', None)
    
    @property
    def kecamatan(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), 'kecamatan', None)

    @property
    def sub_project_name(self) -> str | None:
        return getattr(getattr(self, 'sub_project', None), 'name', None)
    
    @property
    def sub_project_code(self) -> str | None:
        return getattr(getattr(self, 'sub_project', None), 'code', None)
    
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
    def ptsk_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'skpt', None), 'ptsk', None), 'name', None)
    
    @property
    def ptsk_id(self) -> str | None:
        return getattr(getattr(getattr(self, 'skpt', None), 'ptsk', None), 'id', None)
       
    @property
    def no_sk(self) -> str:
        if self.skpt is None:
            return ""
        
        return self.skpt.nomor_sk
    
    @property
    def status_sk(self) -> str:
        if self.skpt is None:
            return None
        
        return self.skpt.status
    
    @property
    def penampung_name(self) -> str | None:
        return getattr(getattr(self, 'penampung', None), 'name', None)
    
    @property
    def manager_name(self) -> str | None:
        return getattr(getattr(self, 'manager', None), 'name', None)
    
    @property
    def sales_name(self) -> str | None:
        return getattr(getattr(self, 'sales', None), 'name', None)
    
    @property
    def notaris_name(self) -> str | None:
        return getattr(getattr(self, 'notaris', None), 'name', None)
    
    @property
    def kjb_harga_akta(self) -> str:
        return getattr(getattr(getattr(self, "hasil_peta_lokasi", None), "kjb_dt", None), "harga_akta", None)
    
    @property
    def kjb_harga_transaksi(self) -> str:
        return getattr(getattr(getattr(self, "hasil_peta_lokasi", None), "kjb_dt", None), "harga_transaksi", None)
    
    # @property
    # def kjb_harga_ptsl(self) -> str:
    #     return getattr(getattr(getattr(self, "hasil_peta_lokasi", None), "kjb_dt", None), "harga_ptsl", None)
    
    @property
    def kjb_no(self) -> str:
        return getattr(getattr(getattr(self, "hasil_peta_lokasi", None), "kjb_dt", None), "kjb_code", None)

    @property
    def hasil_analisa_peta_lokasi(self) -> HasilAnalisaPetaLokasiEnum | None:
        return getattr(getattr(self, "hasil_peta_lokasi", None), "hasil_analisa_peta_lokasi", None)
    
    @property
    def proses_bpn_order_gu(self) -> ProsesBPNOrderGambarUkurEnum | None:
        if self.hasil_peta_lokasi == None:
            return None
        
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Belum_IL and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap:
            return ProsesBPNOrderGambarUkurEnum.PBT_Perorangan
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Belum_IL and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear:
            return ProsesBPNOrderGambarUkurEnum.PBT_Perorangan
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Sudah_Il and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap:
            return ProsesBPNOrderGambarUkurEnum.PBT_Perorangan
        if self.jenis_alashak == JenisAlashakEnum.Girik and self.skpt.status == StatusSKEnum.Sudah_Il and self.hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear:
            return ProsesBPNOrderGambarUkurEnum.PBT_PT
        
        return None
    
    @property
    def total_harga_transaksi(self) -> Decimal | None:
        total_harga_overlap:Decimal = 0
        total_luas_bayar_overlap:Decimal = 0
        harga:Decimal = 0

        if len(self.overlaps) > 0:
            array_total_harga_overlap = [((ov.harga_transaksi or 0) * (ov.luas_bayar or 0)) for ov in self.overlaps if ov.parent_bidang_intersect_id is not None]
            total_harga_overlap = sum(array_total_harga_overlap)

            array_total_luas_bayar_overlap = [(ov.luas_bayar or 0) for ov in self.overlaps if ov.parent_bidang_intersect_id is not None]
            total_luas_bayar_overlap = sum(array_total_luas_bayar_overlap)
        
        # if self.is_ptsl:
        #     harga = self.harga_ptsl
        # else:
        harga = self.harga_transaksi

        return Decimal(((harga or 0) * ((self.luas_bayar or 0) - Decimal(total_luas_bayar_overlap))) + Decimal(total_harga_overlap))
    
    @property
    def total_harga_akta(self) -> Decimal | None:
        total_harga_overlap:Decimal = 0
        total_luas_bayar_overlap:Decimal = 0
        if len(self.overlaps) > 0:
            array_total_harga_overlap = [((ov.harga_transaksi or 0) * (ov.luas_bayar or 0)) for ov in self.overlaps if ov.parent_bidang_intersect_id is not None]
            total_harga_overlap = sum(array_total_harga_overlap)

            array_total_luas_bayar_overlap = [(ov.luas_bayar or 0) for ov in self.overlaps if ov.parent_bidang_intersect_id is not None]
            total_luas_bayar_overlap = sum(array_total_luas_bayar_overlap)

        return Decimal(((self.harga_akta or 0) * ((self.luas_bayar or 0) - Decimal(total_luas_bayar_overlap))) + Decimal(total_harga_overlap))
    
    @property
    def total_beban_penjual(self) -> Decimal | None:
        total_beban_penjual:Decimal = 0
        harga:Decimal = 0

        # if self.is_ptsl:
        #     harga = self.harga_ptsl
        # else:
        harga = self.harga_transaksi

        if len(self.komponen_biayas) > 0:
            calculate = []
            komponen_biaya_beban_penjual = [kb for kb in self.komponen_biayas if kb.beban_pembeli == False and kb.is_void != True and kb.is_paid == True]
            for beban in komponen_biaya_beban_penjual:
                if beban.satuan_bayar == SatuanBayarEnum.Percentage and beban.satuan_harga == SatuanHargaEnum.PerMeter2:
                    amount = (beban.estimated_amount or 0) * ((self.luas_bayar or self.luas_surat) * (harga or 0)/100)
                elif beban.satuan_bayar == SatuanBayarEnum.Amount and beban.satuan_harga == SatuanHargaEnum.PerMeter2:
                    amount = (beban.estimated_amount or 0) * (self.luas_bayar or self.luas_surat)
                else:
                    amount = beban.estimated_amount or 0
                
                calculate.append(Decimal(amount))
            
            total_beban_penjual = sum(calculate) or 0
        
        return Decimal(total_beban_penjual)
    
    @property
    def total_pengembalian_beban_penjual(self) -> Decimal | None:
        total_pengembalian:Decimal = 0
        if len(self.komponen_biayas) > 0:
            komponen_biaya_beban_penjual = [kb.invoice_detail_amount for kb in self.komponen_biayas if kb.beban_pembeli == False and kb.is_void != True and kb.is_retur == True]

            total_pengembalian = (sum(komponen_biaya_beban_penjual) or 0)
        
        return Decimal(total_pengembalian)
            
    @property
    def total_invoice(self) -> Decimal | None:
        total_invoice:Decimal = 0
        if len(self.invoices) > 0:
            list_invoices = [inv.amount_netto for inv in self.invoices if inv.is_void != True]
            total_invoice = Decimal(sum(list_invoices))
        
        return Decimal(total_invoice)
    
    @property
    def nomor_tahap(self) -> int | None:
        if self.tahap is None or self.tahap == 0:
            tahap_detail = next((x for x in self.tahap_details if x.is_void == False), None)

            if tahap_detail:
                return tahap_detail.tahap.nomor_tahap
        else:
            return int(self.tahap)
        
        return None
    
    @property
    def tahap_id(self) -> UUID | None:
        tahap_detail = next((x for x in self.tahap_details if x.is_void == False), None)

        if tahap_detail:
            return tahap_detail.tahap_id
        
        return None
    
    @property
    def total_payment(self) -> Decimal | None:
        total_payment:Decimal = 0
        total_beban_penjual:Decimal = 0

        if len(self.invoices) > 0:
            payments = [payment.amount for invoice in self.invoices if invoice.is_void != True and invoice.jenis_bayar != JenisBayarEnum.BIAYA_LAIN for payment in invoice.payment_details if payment.is_void != True and payment.realisasi != True]
            total_payment = Decimal(sum(payments))
        
        if len(self.komponen_biayas) > 0:
            beban_biayas = [x.invoice_detail_amount for x in self.komponen_biayas if x.is_void != True and x.is_paid == True and x.beban_pembeli == False and x.is_add_pay != True and x.is_retur != True]
            total_beban_penjual = Decimal(sum(beban_biayas))

        return Decimal(total_payment + total_beban_penjual)
    
    @property
    def sisa_pelunasan(self) -> Decimal | None:
        return Decimal(self.total_harga_transaksi - self.total_payment)
    
    #diperlukan untuk spk_amount saat pilih spk di termin
    @property
    def biaya_lain_not_use(self) -> Decimal | None:
        total_biaya_lain:Decimal = 0
        if len(self.komponen_biayas) > 0:
            calculate = []
            calculate = [x.amount_biaya_lain for x in self.komponen_biayas]
            total_biaya_lain = sum(calculate)
        
        return Decimal(total_biaya_lain)
    
    @property
    def sisa_biaya_lain(self) -> Decimal | None:
        total_biaya_lain:Decimal = 0
        if len(self.komponen_biayas) > 0:
            calculate = []
            calculate = [x.amount_biaya_lain for x in self.komponen_biayas]
            total_biaya_lain = sum(calculate)

        total_payment_invoice_biaya_lain:Decimal = 0
        if len(self.invoices) > 0:
            payments = [payment.amount for invoice in self.invoices if invoice.is_void != True and invoice.jenis_bayar == JenisBayarEnum.BIAYA_LAIN for payment in invoice.payment_details if payment.is_void != True]
            total_payment_invoice_biaya_lain = Decimal(sum(payments))
        
        return Decimal(total_biaya_lain - total_payment_invoice_biaya_lain)
    
    @property
    def utj_amount(self) -> Decimal | None:
        utj = 0
        utj_current = next((invoice_utj for invoice_utj in self.invoices 
                            if (invoice_utj.jenis_bayar == JenisBayarEnum.UTJ or invoice_utj.jenis_bayar == JenisBayarEnum.UTJ_KHUSUS) 
                            and invoice_utj.is_void != True), None)
        
        if utj_current:
            amount_payment_details = [payment_detail.amount for payment_detail in utj_current.payment_details if payment_detail.is_void != True and payment_detail.realisasi != True]
            utj = sum(amount_payment_details) or 0
        
        return Decimal(utj)
    
    @property
    def utj_has_use(self) -> bool | None:
        utj = False
        
        invoice_use_utj = next((invoice for invoice in self.invoices if invoice.use_utj == True and invoice.is_void != True), None)
        if invoice_use_utj:
            return True
        
        return utj
    
    @property
    def utj_realisasi_amount(self) -> Decimal | None:
        utj = 0
        utj_current = next((invoice_utj for invoice_utj in self.invoices 
                            if (invoice_utj.jenis_bayar == JenisBayarEnum.UTJ or invoice_utj.jenis_bayar == JenisBayarEnum.UTJ_KHUSUS) 
                            and invoice_utj.is_void != True), None)
        
        if utj_current:
            amount_payment_details = [payment_detail.amount for payment_detail in utj_current.payment_details if payment_detail.is_void != True and payment_detail.realisasi == True]
            utj = sum(amount_payment_details) or 0
        
        return Decimal(utj)
    
    @property
    def has_invoice_lunas(self) -> bool | None:
        invoice_lunas = next((x for x in self.invoices if x.is_void != True and x.jenis_bayar in [JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]), None)
        if invoice_lunas:
            return True
        
        return False
    
    @property
    def has_beginning_balance(self) -> bool | None:
        invoice_beg_bal = next((x for x in self.invoices if x.is_void != True and x.jenis_bayar in [JenisBayarEnum.BEGINNING_BALANCE]), None)
        if invoice_beg_bal and self.sisa_pelunasan == 0:
            return True
        
        return False
    
    @property
    def parent_id_bidang(self) -> str | None:
        if self.parent_bintang:
            return self.parent_bintang.id_bidang
        
    @property
    def parent_alashak(self) -> str | None:
        if self.parent_bintang:
            return self.parent_bintang.alashak
    
    # @property
    # def njop(self) -> Decimal | None:
    #     nilai_njop:Decimal = 0
    #     metadata_njop = next((x for x in self.bundlehd.bundledts if x.dokumen_name == "SPPT NOP PBB"), None)

    #     if not metadata_njop:
    #         return nilai_njop
        
    #     if metadata_njop.meta_data:
    #         if metadata_njop.meta_data is not None and metadata_njop.meta_data != "":
    #             metadata_dict = json.loads(metadata_njop.meta_data.replace("'", "\""))
    #             nilai_njop = Decimal(metadata_dict[f'NJOP'])
            
    #     return nilai_njop


class BidangHistoryBase(SQLModel):
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)

class BidangHistoryBaseExt(BidangHistoryBase, BaseHistoryModel):
    pass

class BidangHistoryFullBase(BaseUUIDModel, BidangHistoryBaseExt):
    pass

class BidangHistory(BidangHistoryFullBase, table=True):
    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        },
        back_populates="bidang_histories"
    )

    trans_worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "BidangHistory.trans_worker_id==Worker.id",
        }
    )

    @property
    def trans_worker_name(self) -> str | None:
        return getattr(getattr(self, "trans_worker", None), "name", None)

class BidangOriginBase(BidangBase):
    geom:str | None = Field(sa_column=Column(Geometry))
    geom_ori:str | None = Field(sa_column=Column(Geometry), nullable=True)

class BidangOriginFullBase(BidangOriginBase):
    id: UUID = Field(primary_key=True, index=True, nullable=False)
    updated_at : datetime | None = Field(default=datetime.now())
    created_at : datetime | None = Field(default=datetime.now())
    created_by_id: UUID | None = Field(default=None, foreign_key='worker.id', nullable=True)
    updated_by_id: UUID | None = Field(default=None, foreign_key='worker.id', nullable=True)

class BidangOrigin(BidangOriginFullBase, table=True):
    pass