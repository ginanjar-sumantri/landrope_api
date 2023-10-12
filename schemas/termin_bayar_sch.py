from models.termin_model import TerminBayar, TerminBayarBase, TerminBayarFullBase
from common.enum import PaymentMethodEnum
from sqlmodel import Field, SQLModel
from uuid import UUID
from decimal import Decimal


class TerminBayarCreateSch(TerminBayarBase):
    pass

class TerminBayarExtSch(SQLModel):
    id:UUID|None
    payment_method:PaymentMethodEnum
    rekening_id:UUID
    amount:Decimal


class TerminBayarSch(TerminBayarFullBase):
    nama_pemilik_rekening:str|None = Field(alias="nama_pemilik_rekening")
    bank_rekening:str|None = Field(alias="bank_rekening")
    nomor_rekening:str|None = Field(alias="nomor_rekening")

class TerminBayarUpdateSch(TerminBayarBase):
    pass