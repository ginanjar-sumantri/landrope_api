from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import PaymentMethodEnum, JenisBayarEnum
from decimal import Decimal
from datetime import date

if TYPE_CHECKING:
    from models import KjbHd, Worker, Payment, Termin

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
    def utj_amount(self) -> Decimal | None:
        return getattr(getattr(self, 'kjb_hd', None), 'utj_amount', None)
    
    @property
    def termin_code(self) -> str | None:
        return getattr(getattr(self, 'termin', None), 'code', None)
    
    @property
    def jumlah_alashak(self) -> int | None:
        if self.termin:
            invoices = [invoice for invoice in self.termin.invoices if invoice.is_void != True]
            return int(len(invoices))
        
        return 0
    
    @property
    def total(self) -> Decimal | None:
        if self.termin:
            invoices = [invoice.amount for invoice in self.termin.invoices if invoice.is_void != True]
            return Decimal(sum(invoices))
        
        return 0