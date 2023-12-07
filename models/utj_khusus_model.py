from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import PaymentMethodEnum, JenisBayarEnum
from decimal import Decimal
from datetime import date

if TYPE_CHECKING:
    from models import KjbHd, Worker, Payment, Termin, KjbDt, Invoice

class UtjKhususBase(SQLModel):
    amount:Decimal = Field(nullable=True)
    code:Optional[str] = Field(nullable=True)
    pay_to: str = Field(nullable=False)
    remark:str | None = Field(nullable=True)
    payment_date:date = Field(nullable=False)

    kjb_hd_id:Optional[UUID] = Field(foreign_key="kjb_hd.id", nullable=True)
    payment_id:UUID|None = Field(foreign_key="payment.id", nullable=False)
    termin_id:UUID|None = Field(foreign_key="termin.id", nullable=False)

class UtjKhususFullBase(BaseUUIDModel, UtjKhususBase):
    pass

class UtjKhusus(UtjKhususFullBase, table=True):
    details:list["UtjKhususDetail"] = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        },
        back_populates="utj_khusus"
    )

    kjb_hd:"KjbHd" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    ) 

    payment:"Payment" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    termin:"Termin" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "UtjKhusus.updated_by_id==Worker.id",
        }
    ) 

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def kjb_hd_code(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'code', None)
    
    @property
    def kjb_hd_group(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'nama_group', None)
    
    @property
    def kjb_hd_mediator(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'mediator', None)
    
    @property
    def utj_amount(self) -> Decimal | None:
        return getattr(getattr(self, 'kjb_hd', None), 'utj_amount', None)
    
    @property
    def luas_kjb(self) -> Decimal | None:
        return getattr(getattr(self, 'kjb_hd', None), 'luas_kjb', None)
    
    @property
    def termin_code(self) -> str | None:
        return getattr(getattr(self, 'termin', None), 'code', None)
    
    @property
    def desa_name(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'desa_name', None)
    
    @property
    def jumlah_alashak(self) -> int | None:
        return int(len(self.details))
    
    @property
    def total(self) -> Decimal | None:
        dt = [detail.amount for detail in self.details]
        return Decimal(sum(dt))
    
class UtjKhususDetailBase(SQLModel):
    utj_khusus_id:UUID|None = Field(foreign_key="utj_khusus.id", nullable=False)
    kjb_dt_id:UUID|None = Field(foreign_key="kjb_dt.id", nullable=False)
    invoice_id:UUID|None = Field(foreign_key="invoice.id", nullable=True)
    amount:Decimal|None = Field(nullable=True)

class UtjKhususDetailFullBase(BaseUUIDModel, UtjKhususDetailBase):
    pass

class UtjKhususDetail(UtjKhususDetailFullBase, table=True):
    utj_khusus:"UtjKhusus" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        },
        back_populates="details"
    )

    kjb_dt:"KjbDt" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )

    invoice:"Invoice" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )

    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, 'kjb_dt', None), 'alashak', None)
    
    @property
    def mediator(self) -> str | None:
        return getattr(getattr(self, 'utj_khusus', None), 'kjb_hd_mediator', None)
    
    @property
    def pemilik_name(self) -> str | None:
        return getattr(getattr(self, 'kjb_dt', None), 'pemilik_name', None)
    
    @property
    def desa_name(self) -> str | None:
        if self.kjb_dt:
            return self.kjb_dt.desa_name if self.kjb_dt.desa_by_ttn is None else self.kjb_dt.desa_name_by_ttn
        return ""
    
    @property
    def project_name(self) -> str | None:
        if self.kjb_dt:
            return self.kjb_dt.project_name if self.kjb_dt.project_by_ttn is None else self.kjb_dt.project_name_by_ttn
        return ""
    
    @property
    def luas_surat(self) -> Decimal | None:
        luas:Decimal = 0
        if self.kjb_dt:
            luas = self.kjb_dt.luas_surat if self.kjb_dt.luas_surat_by_ttn is None else self.kjb_dt.luas_surat_by_ttn

        return luas
    
    @property
    def luas_suratExt(self) -> str | None:
        luas:str = ""
        if self.kjb_dt:
            luas_surat = self.kjb_dt.luas_surat if self.kjb_dt.luas_surat_by_ttn is None else self.kjb_dt.luas_surat_by_ttn
            luas = "{:,.0f}".format(luas_surat)

        return luas
    
    @property
    def amountExt(self) -> str | None:
        return "{:,.0f}".format(self.amount or 0)

    @property
    def luas_bayar(self) -> Decimal | None:
        return getattr(getattr(getattr(getattr(self, 'kjb_dt', None), 'hasil_peta_lokasi', None), 'bidang', None), 'luas_bayar', None)
    
    @property
    def no_peta(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, 'kjb_dt', ""), 'hasil_peta_lokasi', ""), 'bidang', ""), 'no_peta', "")
    
    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, 'kjb_dt', ""), 'hasil_peta_lokasi', ""), 'bidang', ""), 'id_bidang', "")


