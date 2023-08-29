# from sqlmodel import SQLModel, Field
# from sqlalchemy import Column
# from sqlalchemy.dialects.postgresql import TEXT
# from models.base_model import BaseUUIDModel
# from common.enum import TanggunganBiayaEnum
# from uuid import UUID
# from decimal import Decimal
# from pydantic import condecimal

# class KomponenBiayaBase(SQLModel):
#     bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
#     amount:condecimal(decimal_places=2) = Field(default=0)
#     tanggungan:TanggunganBiayaEnum | None = Field(nullable=True)
#     is_tax:bool = Field(default=False)
#     beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
#     remark:str | None = Field(nullable=True, sa_column=Column(TEXT))

# class KomponenBiayaFullBase(BaseUUIDModel, KomponenBiayaBase):
#     pass

# class KomponenBiaya(KomponenBiayaFullBase, table=True):
#     pass