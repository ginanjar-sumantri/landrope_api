from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import PaymentMethodEnum
from decimal import Decimal

if TYPE_CHECKING:
    from giro_model import Giro

class PaymentBase(SQLModel):
    payment_method:Optional[PaymentMethodEnum] = Field(nullable=False)
    amount:Optional[Decimal] = Field(nullable=True)
    giro_id:Optional[UUID] = Field(foreign_key="giro.id")

class PaymentFullBase(BaseUUIDModel, PaymentBase):
    pass

class Payment(PaymentFullBase, table=True):
    giro:"Giro" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )
