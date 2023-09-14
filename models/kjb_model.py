from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
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

class KjbHdBase(SQLModel):
    code:str | None = Field(nullable=True, max_length=500)
    category:CategoryEnum | None
    nama_group:str | None = Field(nullable=True, max_length=200)
    kategori_penjual:KategoriPenjualEnum
    desa_id:UUID = Field(foreign_key="desa.id", nullable=False)
    luas_kjb:Decimal
    tanggal_kjb:date| None = Field(default=date.today())
    remark:str
    manager_id:UUID = Field(foreign_key="manager.id")
    sales_id:UUID = Field(foreign_key="sales.id")
    mediator:str | None
    telepon_mediator:str | None
    ada_utj:bool
    utj_amount:Decimal
    satuan_bayar:SatuanBayarEnum
    satuan_harga:SatuanHargaEnum
    is_draft:Optional[bool] = Field(nullable=True)

class KjbHdFullBase(BaseUUIDModel, KjbHdBase):
    pass

class KjbHd(KjbHdFullBase, table=True):
    desa:"Desa" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    manager:"Manager" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    sales:"Sales" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    kjb_dts:list["KjbDt"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
    rekenings:list["KjbRekening"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
    hargas:list["KjbHarga"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
    bebanbiayas:list["KjbBebanBiaya"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
    penjuals:list["KjbPenjual"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})

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

    desa_id:Optional[UUID] = Field(foreign_key="desa.id", nullable=True)
    desa_by_ttn_id:Optional[UUID] = Field(foreign_key="desa.id", nullable=True)
    project_id:Optional[UUID] = Field(foreign_key="project.id", nullable=True)
    project_by_ttn_id:Optional[UUID] = Field(foreign_key="project.id", nullable=True)
    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)
    pemilik_id:UUID | None = Field(foreign_key="pemilik.id", nullable=True)
    jenis_surat_id:UUID | None = Field(foreign_key="jenis_surat.id", nullable=False)
    bundle_hd_id:UUID | None = Field(foreign_key="bundle_hd.id", nullable=True)


class KjbDtFullBase(BaseUUIDModel, KjbDtBase):
    pass

class KjbDt(KjbDtFullBase, table=True): 
    desa:Optional["Desa"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.desa_id==Desa.id", "lazy": "joined"})
    desa_by_ttn:Optional["Desa"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.desa_by_ttn_id==Desa.id", "lazy": "joined"})
    project:Optional["Project"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.project_id==Project.id", "lazy": "joined"})
    project_by_ttn:Optional["Project"] = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbDt.project_by_ttn_id==Project.id", "lazy": "joined"})
    pemilik:"Pemilik" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    kjb_hd:"KjbHd" = Relationship(back_populates="kjb_dts", sa_relationship_kwargs={'lazy':'selectin'})
    jenis_surat:"JenisSurat" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    bundlehd:"BundleHd" = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'selectin'})
    tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'selectin'})
    request_peta_lokasi:"RequestPetaLokasi" = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'selectin', 'uselist':False})
    hasil_peta_lokasi:"HasilPetaLokasi" = Relationship(
        back_populates="kjb_dt",
        sa_relationship_kwargs=
        {
            "lazy":"selectin",
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

##########################################################################

class KjbPenjualBase(SQLModel):
    pemilik_id:UUID = Field(foreign_key="pemilik.id")
    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbPenjualFullBase(BaseUUIDModel, KjbPenjualBase):
    pass

class KjbPenjual(KjbPenjualFullBase, table=True):
    pemilik:"Pemilik" = Relationship(sa_relationship_kwargs={"primaryjoin": "KjbPenjual.pemilik_id==Pemilik.id", "lazy": "joined"})
    kjb_hd:"KjbHd" = Relationship(back_populates="penjuals", sa_relationship_kwargs={'lazy':'selectin'})

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
    kjb_hd:"KjbHd" = Relationship(back_populates="rekenings", sa_relationship_kwargs={'lazy':'selectin'})

########################################################################################

class KjbHargaBase(SQLModel):
    jenis_alashak:JenisAlashakEnum
    harga_akta:Decimal | None = Field(nullable=True)
    harga_transaksi:Decimal | None = Field(nullable=True)

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id")

class KjbHargaFullBase(BaseUUIDModel, KjbHargaBase):
    pass

class KjbHarga(KjbHargaFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="hargas", sa_relationship_kwargs={'lazy':'selectin'})
    termins:list["KjbTermin"] = Relationship(back_populates="harga", sa_relationship_kwargs={'lazy':'selectin'})

################################################################################################

class KjbTerminBase(SQLModel):
    jenis_bayar:JenisBayarEnum
    nilai:Decimal

    kjb_harga_id:UUID = Field(foreign_key="kjb_harga.id", nullable=False)

class KjbTerminFullBase(BaseUUIDModel, KjbTerminBase):
    pass

class KjbTermin(KjbTerminFullBase, table=True):
    harga:"KjbHarga" = Relationship(back_populates="termins", sa_relationship_kwargs={'lazy':'selectin'})

#################################################################################

class KjbBebanBiayaBase(SQLModel):
    beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
    beban_pembeli:bool = Field(nullable=False)

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbBebanBiayaFullBase(BaseUUIDModel, KjbBebanBiayaBase):
    pass

class KjbBebanBiaya(KjbBebanBiayaFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="bebanbiayas", sa_relationship_kwargs={'lazy':'selectin'})
    beban_biaya:"BebanBiaya" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def beban_biaya_name(self) -> str :
        if self.beban_biaya is None:
            return ""
        
        return self.beban_biaya.name