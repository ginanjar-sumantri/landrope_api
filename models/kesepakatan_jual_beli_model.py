# from sqlmodel import SQLModel, Field, Relationship
# from models.base_model import BaseUUIDModel
# from uuid import UUID
# from typing import TYPE_CHECKING
# from common.enum import CategoryEnum, KategoriPenjualEnum, JenisAlashakEnum, PosisiBidangEnum
# from decimal import Decimal

# if TYPE_CHECKING:
#     from models.planing_model import Planing
#     from models.desa_model import Desa

# class KjbHdBase(SQLModel):
#     kjb_id:str | None = Field(nullable=False, max_length=500)
#     penjual_tanah:str | None = Field(nullable=True, max_length=200)
#     category:CategoryEnum | None
#     nama_group:str | None = Field(nullable=True, max_length=200)
#     kategori_penjual:KategoriPenjualEnum
#     desa_id:UUID = Field(foreign_key="desa.id", nullable=False)
#     luas_kjb:Decimal
#     remark:str
#     manager:UUID = Field(foreign_key="manager.id")
#     sales:UUID = Field(foreign_key="sales.id")
#     mediator:str | None
#     telepon_mediator:str | None
#     pemilik_id:UUID = Field(foreign_key="pemilik.id")
#     kesepakatan_rekening_id:UUID = Field(foreign_key="kesepakatan_rekening.id")

#     is_utj:bool
#     utj_amount:Decimal


# class KjbHdFullBase(BaseUUIDModel, KjbHdBase):
#     pass

# class KjbHd(KjbHdFullBase, table=True):
#     desa:"Desa" = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
#     kjb_dts:list["KjbDt"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})
#     rekenings:list["KesepakatanRekening"] = Relationship(back_populates="kjb_hd", sa_relationship_kwargs={'lazy':'selectin'})

# class KjbDtBase(SQLModel):
#     jenis_alashak:JenisAlashakEnum
#     alashak:str
#     posisi_bidang:PosisiBidangEnum
#     harga_akta:Decimal
#     harga_transaksi:Decimal
#     luas_surat:Decimal

#     kesepakatan_hd_id:UUID = Field(foreign_key="kjb_hd.id", nullable=False)
#     planing_id:UUID | None = Field(foreign_key="planing.id", nullable=True)

# class KjbDtFullBase(BaseUUIDModel, KjbDtBase):
#     pass

# class KjbDt(KjbDtFullBase, table=True):
#     kjb_hd:"KjbHd" = Relationship(back_populates="kjb_dts", sa_relationship_kwargs={'lazy':'selectin'})
#     planing:"Planing" = Relationship(back_populates="kjb_dts", sa_relationship_kwargs={'lazy':'selectin'})

#     @property
#     def planing_name(self) -> str | None :
#         return self.planing.name


# class KesepakatanRekeningBase(SQLModel):
#     nama_pemilik_rekening:str
#     bank_rekening:str
#     nomor_rekening:str

#     kesepakatan_hd_id:UUID = Field(foreign_key="kesepakatan_hd.id", nullable=False)

# class KesepakatanRekeningFullBase(BaseUUIDModel, KesepakatanRekeningBase):
#     pass

# class KesepakatanRekening(KesepakatanRekeningFullBase, table=True):

#     kesepakatanhd:"KjbHd" = Relationship(back_populates="rekenings", sa_relationship_kwargs={'lazy':'selectin'})