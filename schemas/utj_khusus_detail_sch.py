from models.utj_khusus_model import UtjKhususDetail, UtjKhususDetailBase, UtjKhususDetailFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID

class UtjKhususDetailCreateSch(UtjKhususDetailBase):
    pass

class UtjKhususDetailExtSch(SQLModel):
    id:UUID|None
    kjb_dt_id:UUID
    invoice_id:UUID|None
    amount:Decimal|None


class UtjKhususDetailSch(UtjKhususDetailFullBase):
    id_bidang:str|None
    no_peta:str|None
    mediator:str|None
    alashak:str|None = Field(alias="alashak")
    luas_surat:Decimal|None = Field(alias="luas_surat")
    luas_bayar:Decimal|None = Field(alias="luas_bayar")
    luas_suratExt:str|None
    amountExt:str|None
    desa_name:str|None
    project_name:str|None
    pemilik_name:str|None

@optional
class UtjKhususDetailUpdateSch(UtjKhususDetailBase):
    pass