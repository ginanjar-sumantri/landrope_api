from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import ProsesOrderGambarUkur
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.worker_model import Worker
    from models.notaris_model import Notaris
    from models.bidang_model import Bidang

class OrderGambarUkurBase(SQLModel):
    code:str
    tujuan_surat_worker_id:UUID | None = Field(nullable=True, foreign_key="worker.id")
    tujuan_surat_notaris_id:UUID | None = Field(nullable=True, foreign_key="notaris.id")

class OrderGambarUkurFullBase(BaseUUIDModel, OrderGambarUkurBase):
    pass

class OrderGambarUkur(OrderGambarUkurFullBase, table=True):
    worker_tujuan:"Worker" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "joined",
            "primaryjoin" : "OrderGambarUkur.tujuan_surat_worker_id == Worker.id"
        }
    )

    notaris_tujuan:"Notaris" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    bidangs:list["OrderGambarUkurBidang"] = Relationship(
        back_populates="order_gambar_ukur",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )


class OrderGambarUkurBidangBase(SQLModel):
    order_gambar_ukur_id:UUID = Field(nullable=False, foreign_key="order_gambar_ukur.id")
    bidang_id:UUID = Field(nullable=False, foreign_key="bidang.id")
    proses_order:ProsesOrderGambarUkur
    perihal:str

class OrderGambarUkurBidangFullBase(BaseUUIDModel, OrderGambarUkurBidangBase):
    pass

class OrderGambarUkurBidang(OrderGambarUkurBidangFullBase, table=True):
    order_gambar_ukur:"OrderGambarUkur" = Relationship(
        back_populates="bidangs",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

class OrderGambarUkurTembusanBase(SQLModel):
    order_gambar_ukur_id:UUID = Field(nullable=False, foreign_key="order_gambar_ukur.id")
    tembusan_id:UUID = Field(nullable=False, foreign_key="worker.id")
