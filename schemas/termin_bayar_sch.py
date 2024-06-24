from models.termin_model import TerminBayar, TerminBayarBase, TerminBayarFullBase
from schemas.termin_bayar_dt_sch import TerminBayarDtExtSch
from common.enum import PaymentMethodEnum, ActivityEnum
from sqlmodel import Field, SQLModel
from uuid import UUID
from decimal import Decimal
from pydantic import validator


class TerminBayarCreateSch(TerminBayarBase):
    pass

class TerminBayarExtSch(SQLModel):
    id:UUID|None
    id_index: UUID | None
    payment_method:PaymentMethodEnum
    rekening_id:UUID|None
    amount:Decimal | None
    remark:str | None
    activity: ActivityEnum | None
    name: str | None
    pay_to: str | None
    termin_bayar_dts: list[TerminBayarDtExtSch] | None


class TerminBayarSch(TerminBayarFullBase):
    nama_pemilik_rekening:str|None = Field(alias="nama_pemilik_rekening")
    bank_rekening:str|None = Field(alias="bank_rekening")
    nomor_rekening:str|None = Field(alias="nomor_rekening")

class TerminBayarForPrintout(TerminBayarSch):
    amountExt:str|None = Field(alias="amountExt")

class TerminBayarUpdateSch(TerminBayarBase):
    pass