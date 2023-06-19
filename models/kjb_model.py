from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import CategoryEnum, KategoriPenjualEnum, JenisAlashakEnum, PosisiBidangEnum, SatuanBayarEnum, JenisBayarEnum
from decimal import Decimal
from datetime import datetime

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.desa_model import Desa
    from models.marketing_model import Manager, Sales
    from models.pemilik_model import Pemilik
    from models.master_model import JenisSurat
    from models.tanda_terima_notaris_model import TandaTerimaNotarisHd
    from models.bundle_model import BundleHd

class KjbHdBase(SQLModel):
    kjb_id:str | None = Field(nullable=False, max_length=500)
    penjual_tanah:str | None = Field(nullable=True, max_length=200)
    category:CategoryEnum | None
    nama_group:str | None = Field(nullable=True, max_length=200)
    kategori_penjual:KategoriPenjualEnum
    desa_id:UUID = Field(foreign_key="desa.id", nullable=False)
    luas_kjb:Decimal
    tanggal_kjb:datetime| None = Field(default=datetime.now())
    remark:str
    manager_id:UUID = Field(foreign_key="manager.id")
    sales_id:UUID = Field(foreign_key="sales.id")
    mediator:str | None
    telepon_mediator:str | None
    pemilik_id:UUID = Field(foreign_key="pemilik.id")
    ada_utj:bool
    utj_amount:Decimal
    satuan_bayar:SatuanBayarEnum

class KjbHdFullBase(BaseUUIDModel, KjbHdBase):
    pass

class KjbHd(KjbHdFullBase, table=True):
    desa:"Desa" = Relationship(back_populates="kjb_hds", sa_relationship_kwargs={'lazy':'selectin'})
    manager:"Manager" = Relationship(back_populates="kjb_hds", sa_relationship_kwargs={'lazy':'selectin'})
    sales:"Sales" = Relationship(back_populates="kjb_hds", sa_relationship_kwargs={'lazy':'selectin'})
    pemilik:"Pemilik" = Relationship(back_populates="kjb_hds", sa_relationship_kwargs={'lazy':'selectin'})

    kjb_dts:list["KjbDt"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
    rekenings:list["KjbRekening"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
    carabayars:list["KjbCaraBayar"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
    bebanbiayas:list["KjbBebanBiaya"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})

    tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def desa_name(self) -> str | None:
        return self.desa.name
    
    @property
    def manager_name(self) -> str | None:
        return self.manager.name
    
    @property
    def sales_name(self) -> str | None:
        return self.sales.name
    
    @property
    def nomor_telepon(self) -> list[str] | None:
        kontaks = []
        for i in self.pemilik.kontaks:
            kontaks.append(i.nomor_telepon)
        
        return kontaks


class KjbDtBase(SQLModel):
    jenis_alashak:JenisAlashakEnum
    alashak:str
    posisi_bidang:PosisiBidangEnum
    harga_akta:Decimal
    harga_transaksi:Decimal
    luas_surat:Decimal
    
    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)
    planing_id:UUID | None = Field(foreign_key="planing.id", nullable=True)
    jenis_surat_id:UUID = Field(foreign_key="jenis_surat.id", nullable=False)
    bundle_hd_id:UUID = Field(foreign_key="bundle_hd.id", nullable=True)


class KjbDtFullBase(BaseUUIDModel, KjbDtBase):
    pass

class KjbDt(KjbDtFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="kjb_dts", sa_relationship_kwargs={'lazy':'selectin'})
    planing:"Planing" = Relationship(back_populates="kjb_dts", sa_relationship_kwargs={'lazy':'selectin'})
    jenis_surat:"JenisSurat" = Relationship(back_populates="kjb_dts", sa_relationship_kwargs={'lazy':'selectin'})
    bundlehd:"BundleHd" = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'selectin'})

    tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="kjb_dt", sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def planing_name(self) -> str | None :
        return self.planing.name
    
    @property
    def jenis_surat_name(self) -> str | None :
        return self.jenis_surat.name


class KjbRekeningBase(SQLModel):
    nama_pemilik_rekening:str
    bank_rekening:str
    nomor_rekening:str

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbRekeningFullBase(BaseUUIDModel, KjbRekeningBase):
    pass

class KjbRekening(KjbRekeningFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="rekenings", sa_relationship_kwargs={'lazy':'selectin'})


class KjbCaraBayarBase(SQLModel):
    jenis_bayar:JenisBayarEnum
    nilai:Decimal

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbCaraBayarFullBase(BaseUUIDModel, KjbCaraBayarBase):
    pass

class KjbCaraBayar(KjbCaraBayarFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="carabayars", sa_relationship_kwargs={'lazy':'selectin'})


class KjbBebanBiayaBase(SQLModel):
    beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
    beban_pembeli:bool = Field(nullable=False)

    kjb_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)

class KjbBebanBiayaFullBase(BaseUUIDModel, KjbBebanBiayaBase):
    pass

class KjbBebanBiaya(KjbBebanBiayaFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="bebanbiayas", sa_relationship_kwargs={'lazy':'selectin'})