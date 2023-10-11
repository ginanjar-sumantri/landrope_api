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
    code:str = Field(sa_column=(Column("code", String, unique=True)), nullable=False)
    amount:condecimal(decimal_places=2) = Field(nullable=False, default=0)
    is_active:bool = Field(default=True)

class GiroFullBase(BaseUUIDModel, GiroBase):
    pass

class Giro(GiroFullBase, table=True):
    payments:list["Payment"] = Relationship(
        back_populates="giro",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def giro_outstanding(self) -> Decimal | None:
        total_payment:Decimal = 0
        if len(self.payments) > 0:
            array_payment = numpy.array([payment.amount for payment in self.payments if payment.is_void != True])
            total_payment = Decimal(numpy.sum(array_payment))
        
        return self.amount - total_payment