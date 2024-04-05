from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String
from models.base_model import BaseUUIDModel
from common.enum import PaymentMethodEnum
from uuid import UUID
from pydantic import condecimal
from typing import TYPE_CHECKING
from decimal import Decimal
from datetime import date
import numpy

if TYPE_CHECKING:
    from models import Payment, PaymentGiroDetail

class GiroBase(SQLModel):
    code:str|None = Field(sa_column=(Column("code", String, unique=True)), nullable=False)
    nomor_giro:str|None = Field(sa_column=(Column("nomor_giro", String, unique=True)), nullable=False)
    amount: Decimal | None = Field(nullable=False, default=0)
    is_active:bool|None = Field(default=True)
    from_master:bool|None = Field(nullable=True) #create from

    tanggal:date|None = Field(nullable=True)
    bank_code:str|None = Field(nullable=True)
    payment_method:PaymentMethodEnum|None = Field(nullable=True)
    tanggal_buka:date|None = Field(nullable=True)
    tanggal_cair:date|None = Field(nullable=True)


class GiroFullBase(BaseUUIDModel, GiroBase):
    pass

class Giro(GiroFullBase, table=True):
    payment:list["Payment"] = Relationship(
        back_populates="giro",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    payment_giros:list["PaymentGiroDetail"] = Relationship(
        back_populates="giro",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )



    @property
    def is_used(self) -> bool | None:
        # if len(self.payment) > 0:
        #     return True
        used = next((y for x in self.payment for y in x.details if y.is_void != True), None)
        if used:
            return True
        
        used = next((y for x in self.payment_giros for y in x.payment_details if y.is_void != True), None)
        if used:
            return True
        
        return False
    
    @property
    def payment_code(self) -> str | None:
        if len(self.payment) > 0:
            payment = next((x for x in self.payment if x.is_void != True), None)
            if payment:
                return payment.code
            
        return None
    
    # @property
    # def giro_outstanding(self) -> Decimal | None:
    #     total_payment:Decimal = 0
    #     if len(self.payments) > 0:
    #         array_payment = [payment.amount for payment in self.payments if payment.is_void != True]
    #         total_payment = sum(array_payment)
        
    #     return Decimal(self.amount - Decimal(total_payment))

    
    @property
    def giro_used(self) -> Decimal | None:
        total_payment:Decimal = 0
        if len(self.payment) > 0:
            array_payment = [pay.amount for pay in self.payment if pay.is_void != True]
            total_payment = sum(array_payment)

        return Decimal(total_payment)