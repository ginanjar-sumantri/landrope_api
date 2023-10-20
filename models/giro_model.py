from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String
from models.base_model import BaseUUIDModel
from uuid import UUID
from pydantic import condecimal
from typing import TYPE_CHECKING
from decimal import Decimal
import numpy

if TYPE_CHECKING:
    from models import Payment

class GiroBase(SQLModel):
    code:str|None = Field(sa_column=(Column("code", String, unique=True)), nullable=False)
    nomor_giro:str|None = Field(sa_column=(Column("nomor_giro", String, unique=True)), nullable=False)
    amount:condecimal(decimal_places=2) = Field(nullable=False, default=0)
    is_active:bool = Field(default=True)
    from_master:bool|None = Field(nullable=True) #create from

class GiroFullBase(BaseUUIDModel, GiroBase):
    pass

class Giro(GiroFullBase, table=True):
    payment:"Payment" = Relationship(
        back_populates="giro",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def is_used(self) -> bool | None:
        if self.payment:
            return True
        
        return False
    
    @property
    def payment_code(self) -> str | None:
        return getattr(getattr(self, "payment", None), "code", None)

    # @property
    # def giro_outstanding(self) -> Decimal | None:
    #     total_payment:Decimal = 0
    #     if len(self.payments) > 0:
    #         array_payment = [payment.amount for payment in self.payments if payment.is_void != True]
    #         total_payment = sum(array_payment)
        
    #     return Decimal(self.amount - Decimal(total_payment))

    
    # @property
    # def giro_used(self) -> Decimal | None:
    #     total_payment:Decimal = 0
    #     if len(self.payments) > 0:
    #         array_payment = [payment.amount for payment in self.payments if payment.is_void != True]
    #         total_payment = sum(array_payment)

    #     return Decimal(total_payment)