from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import PaymentMethodEnum, JenisBayarEnum
from decimal import Decimal
from datetime import date

if TYPE_CHECKING:
    from models import KjbHd, Worker, Payment

class UtjKhususBase(SQLModel):
    amount:Decimal = Field(nullable=True)
    code:Optional[str] = Field(nullable=True)
    pay_to: str = Field(nullable=False)
    remark:str | None = Field(nullable=True)
    payment_date:date = Field(nullable=False)

    kjb_hd_id:Optional[UUID] = Field(foreign_key="kjb_hd.id", nullable=True)
    payment_id:UUID|None = Field(foreign_key="payment.id", nullable=False)

class UtjKhususFullBase(BaseUUIDModel, UtjKhususBase):
    pass

class UtjKhusus(UtjKhususFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(
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

    payment:"Payment" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def kjb_hd_code(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'code', None)