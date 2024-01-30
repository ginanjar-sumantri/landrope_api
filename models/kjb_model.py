from sqlmodel import SQLModel, Field, Relationship, select
from models.base_model import BaseUUIDModel, BaseHistoryModel
from sqlalchemy import Column, String
from sqlalchemy.orm import column_property, declared_attr
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from models.workflow_model import Workflow
from common.enum import (CategoryEnum, KategoriPenjualEnum, JenisAlashakEnum, 
                         PosisiBidangEnum, SatuanBayarEnum, SatuanHargaEnum, 
                         JenisBayarEnum, StatusPetaLokasiEnum)
from common.rounder import RoundTwo
from decimal import Decimal
from datetime import datetime, date
from pydantic import validator
from dateutil import tz
import pytz

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.desa_model import Desa
    from models.project_model import Project
    from models.marketing_model import Manager, Sales
    from models.pemilik_model import Pemilik
    from models.master_model import JenisSurat, BebanBiaya
    from models.tanda_terima_notaris_model import TandaTerimaNotarisHd
    from models.bundle_model import BundleHd
    from models.request_peta_lokasi_model import RequestPetaLokasi
    from models.worker_model import Worker
    from models.hasil_peta_lokasi_model import HasilPetaLokasi
    from models.spk_model import Spk

class KjbHdBase(SQLModel):
    code:str | None = Field(sa_column=(Column("code", String, unique=True)), nullable=False)
    category:CategoryEnum | None = Field(nullable=True)
    nama_group:str | None = Field(nullable=True, max_length=200)
    kategori_penjual:KategoriPenjualEnum | None = Field(nullable=True)
    desa_id:UUID | None = Field(foreign_key="desa.id", nullable=True)
    luas_kjb:Decimal | None = Field(nullable=True)
    tanggal_kjb:date| None = Field(default=date.today(), nullable=True)
    remark:str | None = Field(nullable=True)
    manager_id:UUID | None = Field(foreign_key="manager.id", nullable=True)
    sales_id:UUID | None = Field(foreign_key="sales.id", nullable=True)
    mediator:str | None = Field(nullable=True)
    telepon_mediator:str | None = Field(nullable=True)
    ada_utj:bool | None = Field(nullable=True)
    utj_amount:Decimal | None = Field(nullable=True)
    satuan_bayar:SatuanBayarEnum | None = Field(nullable=True)
    satuan_harga:SatuanHargaEnum | None = Field(nullable=True)
    file_path:str | None = Field(nullable=True)
    is_draft:Optional[bool] = Field(nullable=True)

class KjbHdFullBase(BaseUUIDModel, KjbHdBase):
    pass

class KjbHd(KjbHdFullBase, table=True):
    desa:"Desa" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    manager:"Manager" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    sales:"Sales" = Relationship(sa_relationship_kwargs={'lazy':'select'})

    kjb_dts:list["KjbDt"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'select'})
    rekenings:list["KjbRekening"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'select'})
    hargas:list["KjbHarga"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'select'})
    bebanbiayas:list["KjbBebanBiaya"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'select'})
    penjuals:list["KjbPenjual"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'select'})
    kjb_histories:list["KjbHistory"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'select'})

    # tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "KjbHd.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def desa_name(self) -> str | None:
        if self.desa is None:
            return ""
        return self.desa.name
    
    @property
    def manager_name(self) -> str | None:
        if self.manager is None:
            return ""
        return self.manager.name
    
    @property
    def sales_name(self) -> str | None:
        if self.sales is None:
            return ""
        return self.sales.name
    
    @property
    def total_luas_surat(self) -> Decimal:
        if len(self.kjb_dts) > 0:
            total_luas = sum(item.luas_surat for item in self.kjb_dts)
            return RoundTwo(total_luas)
        else:
            return RoundTwo(0)    

    @declared_attr
    def step_name_workflow(self) -> column_property:
        return column_property(
            select(
                Workflow.step_name
            )
            .select_from(
                Workflow)
            .where(Workflow.reference_id == self.id)
            .scalar_subquery()
        )
    
    @declared_attr
    def status_workflow(self) -> column_property:
        return column_property(
            select(
                Workflow.last_status
            )
            .select_from(
                Workflow)
            .where(Workflow.reference_id == self.id)
            .scalar_subquery()
        )    


##########################################################################

class KjbDtBase(SQLModel):
    jenis_alashak:JenisAlashakEnum
    alashak:str
    posisi_bidang:PosisiBidangEnum
    harga_akta:Decimal
    harga_transaksi:Decimal
    luas_surat:Decimal
    luas_surat_by_ttn:Decimal | None = Field(nullable=True)
    status_peta_lokasi:StatusPetaLokasiEnum | None = Field(nullable=True)
    group:str|None = Field(nullable=True)

    desa_id:Optional[UUID] = Field(foreign_key="desa.id", nullable=True)
    desa_by_ttn_id:Optional[UUID] = Field(foreign_key="desa.id", nullable=True)
    project_id:Optional[UUID] = Field(foreign_key="project.id", nullable=True)
    project_by_ttn_id:Optional[UUID] = Field(foreign_key="project.id", nullable=True)
    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)
    pemilik_id:UUID | None = Field(foreign_key="pemilik.id", nullable=True)
    jenis_surat_id:UUID | None = Field(foreign_key="jenis_surat.id", nullable=False)
    bundle_hd_id:UUID | None = Field(foreign_key="bundle_hd.id", nullable=True)
    jumlah_waris:int|None = Field(nullable=True)


class KjbDtFullBase(BaseUUIDModel, KjbDtBase):
    pass

class KjbDt(KjbDtFullBase, table=True): 
    desa:Optional["Desa"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.desa_id==Desa.id", "lazy": "joined"})
    desa_by_ttn:Optional["Desa"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.desa_by_ttn_id==Desa.id", "lazy": "joined"})
    project:Optional["Project"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.project_id==Project.id", "lazy": "joined"})
    project_by_ttn:Optional["Project"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.project_by_ttn_id==Project.id", "lazy": "joined"})
    pemilik:"Pemilik" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    kjb_hd:"KjbHd" = Relationship(back_populates="kjb_dts", sa_relationship_kwargs={'lazy':'select'})
    jenis_surat:"JenisSurat" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    bundlehd:"BundleHd" = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'select'})
    tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'select'})
    request_peta_lokasi:"RequestPetaLokasi" = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'select', 'uselist':False})
    hasil_peta_lokasi:"HasilPetaLokasi" = Relationship(
        back_populates="kjb_dt",
        sa_relationship_kwargs=
        {
            "lazy":"select",
            "uselist":False
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "KjbDt.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def desa_name(self) -> str | None :
        if self.desa is None:
            return ""
        return self.desa.name
    
    @property
    def desa_name_by_ttn(self) -> str :
        if self.desa_by_ttn is None:
            return ""
        
        return self.desa_by_ttn.name
    
    @property
    def project_name(self) -> str | None :
        if self.project is None:
            return ""
        return self.project.name
    
    @property
    def project_name_by_ttn(self) -> str :
        if self.project_by_ttn is None:
            return ""
        
        return self.project_by_ttn.name
    
    @property
    def jenis_surat_name(self) -> str | None :
        return self.jenis_surat.name
    
    @property
    def kjb_code(self) -> str :
        return self.kjb_hd.code
    
    @property
    def kategori_penjual(self) -> str:
        return str(self.kjb_hd.kategori_penjual)
    
    @property
    def done_request_petlok(self) -> bool:
        status = False

        if self.request_peta_lokasi:
            status = True
        
        return status
    
    @property
    def has_input_petlok(self) -> bool:
        if self.hasil_peta_lokasi:
            return True
        
        return False
    
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
    
    @property
    def luas_surat(self) -> Decimal | None:
        if self.hasil_peta_lokasi:
            return self.hasil_peta_lokasi.bidang.luas_surat
        else:
            return self.luas_surat_by_ttn
    
    @property
    def bundle_dt_alashak_id(self) -> UUID | None:
        if self.bundlehd:
            alashak = next((als for als in self.bundlehd.bundledts if als.dokumen_name == "ALAS HAK"), None)
            if alashak:
                return alashak.id
        
        return None
    
    @property
    def bundle_dt_alashak_file_exists(self) -> bool | None:
        if self.bundlehd:
            alashak = next((als for als in self.bundlehd.bundledts if als.dokumen_name == "ALAS HAK"), None)
            if alashak:
                return alashak.file_exists
        
        return False
    
    @property
    def bundle_dt_alashak_file_path(self) -> str | None:
        if self.bundlehd:
            alashak = next((als for als in self.bundlehd.bundledts if als.dokumen_name == "ALAS HAK"), None)
            if alashak:
                return alashak.file_path
        
        return None
    
    @property
    def kjb_hd_group(self) -> str | None:
        return getattr(getattr(self, "kjb_hd", None), "nama_group", None)
    
    @property
    def tanggal_kirim_ukur(self) -> date | None:
        return getattr(getattr(self, "request_peta_lokasi", None), "tanggal_kirim_ukur", None)
    
    @property
    def tanggal_terima_berkas(self) -> date | None:
        return getattr(getattr(self, "request_peta_lokasi", None), "tanggal_terima_berkas", None)
    
    @property
    def tanggal_pengukuran(self) -> date | None:
        return getattr(getattr(self, "request_peta_lokasi", None), "tanggal_pengukuran", None)
    
    @property
    def penunjuk_batas(self) -> str | None:
        return getattr(getattr(self, "request_peta_lokasi", None), "penunjuk_batas", None)
    
    @property
    def surveyor(self) -> str | None:
        return getattr(getattr(self, "request_peta_lokasi", None), "surveyor", None)

##########################################################################

class KjbPenjualBase(SQLModel):
    pemilik_id:UUID = Field(foreign_key="pemilik.id")
    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbPenjualFullBase(BaseUUIDModel, KjbPenjualBase):
    pass

class KjbPenjual(KjbPenjualFullBase, table=True):
    pemilik:"Pemilik" = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbPenjual.pemilik_id==Pemilik.id", "lazy": "joined"})
    kjb_hd:"KjbHd" = Relationship(back_populates="penjuals", sa_relationship_kwargs={'lazy':'select'})

    @property
    def penjual_tanah(self) -> str | None:
        if self.pemilik is None:
            return ""
        return self.pemilik.name

###########################################################################
    
class KjbRekeningBase(SQLModel):
    nama_pemilik_rekening:str
    bank_rekening:str
    nomor_rekening:str

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbRekeningFullBase(BaseUUIDModel, KjbRekeningBase):
    pass

class KjbRekening(KjbRekeningFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="rekenings", sa_relationship_kwargs={'lazy':'select'})

########################################################################################

class KjbHargaBase(SQLModel):
    jenis_alashak:JenisAlashakEnum
    harga_akta:Decimal | None = Field(nullable=True)
    harga_transaksi:Decimal | None = Field(nullable=True)

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id")

class KjbHargaFullBase(BaseUUIDModel, KjbHargaBase):
    pass

class KjbHarga(KjbHargaFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="hargas", sa_relationship_kwargs={'lazy':'select'})

    termins:list["KjbTermin"] = Relationship(back_populates="harga", 
                                            sa_relationship_kwargs={
                                                'lazy':'select',
                                                "cascade" : "delete, all",
                                                "foreign_keys" : "[KjbTermin.kjb_harga_id]"
                                            }
                                            )
    

################################################################################################

class KjbTerminBase(SQLModel):
    jenis_bayar:JenisBayarEnum
    nilai:Decimal

    kjb_harga_id:UUID = Field(foreign_key="kjb_harga.id", nullable=False)

class KjbTerminFullBase(BaseUUIDModel, KjbTerminBase):
    pass

class KjbTermin(KjbTerminFullBase, table=True):
    harga:"KjbHarga" = Relationship(back_populates="termins", sa_relationship_kwargs={'lazy':'select'})
    spks:list["Spk"] = Relationship(back_populates="kjb_termin", sa_relationship_kwargs={'lazy':'select'})


    @property
    def has_been_spk(self) -> bool:
        if len(self.spks) > 0:
            return True
        
        return False


#################################################################################

class KjbBebanBiayaBase(SQLModel):
    beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
    beban_pembeli:bool = Field(nullable=False)

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbBebanBiayaFullBase(BaseUUIDModel, KjbBebanBiayaBase):
    pass

class KjbBebanBiaya(KjbBebanBiayaFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="bebanbiayas", sa_relationship_kwargs={'lazy':'select'})
    beban_biaya:"BebanBiaya" = Relationship(sa_relationship_kwargs={'lazy':'select'})

    @property
    def beban_biaya_name(self) -> str :
        if self.beban_biaya is None:
            return ""
        
        return self.beban_biaya.name
    
    @property
    def is_tax(self) -> bool | None :
        return getattr(getattr(self, "beban_biaya", False), "is_tax", False)
    
    @property
    def is_add_pay(self) -> bool | None :
        return getattr(getattr(self, "beban_biaya", False), "is_add_pay", False)
    
###################################################################################################################

class KjbHistoryBase(SQLModel):
    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbHistoryBaseExt(KjbHistoryBase, BaseHistoryModel):
    pass

class KjbHistoryFullBase(BaseUUIDModel, KjbHistoryBaseExt):
    pass

class KjbHistory(KjbHistoryFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        },
        back_populates="kjb_histories"
    )

    trans_worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "KjbHistory.trans_worker_id==Worker.id",
        }
    )

    @property
    def trans_worker_name(self) -> str | None:
        return getattr(getattr(self, "trans_worker", None), "name", None)
    