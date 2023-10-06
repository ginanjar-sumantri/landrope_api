from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import PaymentMethodEnum
from decimal import Decimal

if TYPE_CHECKING:
    from models import Giro, Worker, Invoice

class PaymentBase(SQLModel):
    payment_method:Optional[PaymentMethodEnum] = Field(nullable=False)
    amount:Optional[Decimal] = Field(nullable=True)
    giro_id:Optional[UUID] = Field(foreign_key="giro.id")
    code:Optional[str] = Field(nullable=True)

class PaymentFullBase(BaseUUIDModel, PaymentBase):
    pass

class Payment(PaymentFullBase, table=True):
    details:list["PaymentDetail"] = Relationship(
        back_populates="payment",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    giro:"Giro" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Payment.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

class PaymentDetailBase(SQLModel):
    payment_id:UUID = Field(foreign_key="payment.id")
    invoice_id:UUID = Field(foreign_key="invoice.id")
    amount:Optional[Decimal] = Field(default=0, nullable=True)
    is_void:Optional[bool] = Field(default=False, nullable=False)
    void_by:Optional[UUID] = Field(foreign_key="worker.id", nullable=True)

class PaymentDetailFullBase(BaseUUIDModel, PaymentDetailBase):
    pass

class PaymentDetail(PaymentDetailFullBase, table=True):
    payment:"Payment" = Relationship(
        back_populates="details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    invoice:"Invoice" = Relationship(
        back_populates="payment_details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    worker_do_void: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PaymentDetail.void_by==Worker.id",
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PaymentDetail.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def void_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker_do_void', None), 'name', None)
    
    @property
    def code(self) -> str | None:
        if self.payment.giro:
            return self.payment.giro.code
        
        return self.payment.code
    
    @property
    def payment_method(self) -> PaymentMethodEnum | None:
        return getattr(getattr(self, "payment", None), "payment_method", None)
