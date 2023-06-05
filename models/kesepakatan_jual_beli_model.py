from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import CategoryEnum, KategoriPenjualEnum
from decimal import Decimal

class KesepakatanHd(SQLModel):
    kjb_id:str | None = Field(nullable=False, max_length=500)
    penjual_tanah:str | None = Field(nullable=True, max_length=200)
    category:CategoryEnum | None
    nama_group:str | None = Field(nullable=True, max_length=200)
    kategori_penjual:KategoriPenjualEnum
    desa_id:UUID = Field(foreign_key="desa.id", nullable=False)
    luas_kjb:Decimal
    remark:str

    
