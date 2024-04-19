from models.master_model import BebanBiaya, BebanBiayaBase, BebanBiayaFullBase
from common.partial import optional
from common.enum import SatuanBayarEnum, SatuanHargaEnum
from pydantic import BaseModel
from sqlmodel import Field, SQLModel
from uuid import UUID
from decimal import Decimal

class BebanBiayaCreateSch(BebanBiayaBase):
    pass

class BebanBiayaSch(BebanBiayaFullBase):
    updated_by_name2:str|None = Field(alias="updated_by_name")


class BebanBiayaForSpkSch(SQLModel):
    beban_biaya_id:UUID|None
    beban_pembeli:bool|None
    beban_biaya_name:str|None
    is_tax:bool|None
    is_void:bool|None = Field(default=False)
    is_add_pay:bool|None = Field(default=False)
    is_retur:bool|None = Field(default=False)


@optional
class BebanBiayaUpdateSch(BebanBiayaBase):
    pass

class BebanBiayaGroupingSch(SQLModel):
    beban_biaya_id:UUID | None
    beban_biaya_name:str | None
    amount:Decimal | None
    memo_code:str | None
    nomor_memo:str | None
    termin_id:UUID | None
    payment_giro_detail_id:UUID | None
    giro_id: UUID | None
    nomor_giro: str | None

class BebanBiayaEstimatedAmountSch(BebanBiayaBase):
    estimated_amount: Decimal | None
    bidang_id: UUID | None

