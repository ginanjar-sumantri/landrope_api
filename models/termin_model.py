from sqlmodel import SQLModel, Field, Relationship, select
from sqlalchemy.orm import column_property, declared_attr, aliased
from models.base_model import BaseUUIDModel
from models.workflow_model import Workflow
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum, PaymentMethodEnum, ActivityEnum
from decimal import Decimal
from datetime import date, datetime
import numpy

if TYPE_CHECKING:
    from models import Tahap, KjbHd, Worker, Invoice, Notaris, Manager, Sales, Rekening, InvoiceBayar, BebanBiaya

class TerminBase(SQLModel):
    code:Optional[str] = Field(nullable=True)
    nomor_memo:Optional[str] = Field(nullable=True)
    tahap_id:Optional[UUID] = Field(foreign_key="tahap.id", nullable=True)
    kjb_hd_id:Optional[UUID] = Field(foreign_key="kjb_hd.id", nullable=True)
    jenis_bayar:JenisBayarEnum = Field(nullable=True)
    # amount:Optional[Decimal] = Field(nullable=True)
    is_void:Optional[bool] = Field(nullable=False)
    tanggal_rencana_transaksi:Optional[date] = Field(nullable=True) #tanggal rencana transaksi
    tanggal_transaksi:Optional[date] = Field(nullable=True)
    notaris_id:Optional[UUID] = Field(nullable=True, foreign_key="notaris.id")
    manager_id:Optional[UUID] = Field(nullable=True, foreign_key="manager.id")
    sales_id:Optional[UUID] = Field(nullable=True, foreign_key="sales.id")
    mediator:Optional[str] = Field(nullable=True)
    remark:Optional[str] = Field(nullable=True)
    void_by_id:Optional[UUID] = Field(foreign_key="worker.id", nullable=True)
    void_reason:Optional[str] = Field(nullable=True)
    void_at:Optional[date] = Field(nullable=True)
    file_path:str | None = Field(nullable=True)
    file_upload_path:str | None = Field(nullable=True)
    is_draft: bool | None = Field(nullable=True)

    rfp_ref_no: str | None = Field(nullable=True)
    rfp_last_status: str | None = Field(nullable=True)

    # workflow_id: UUID | str | None = Field(foreign_key="workflow.id", nullable=True)

class TerminFullBase(BaseUUIDModel, TerminBase):
    pass

class Termin(TerminFullBase, table=True):
    invoices:list["Invoice"] = Relationship(
        back_populates="termin",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    tahap:"Tahap" = Relationship(
        back_populates="termins",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    kjb_hd:"KjbHd" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    notaris:"Notaris" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    manager:"Manager" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    sales:"Sales" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    termin_bayars:list["TerminBayar"] = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Termin.updated_by_id==Worker.id",
        }
    )

    worker_do_void: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Termin.void_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def nomor_tahap(self) -> int | None:
        return getattr(getattr(self, 'tahap', None), 'nomor_tahap', None)
    
    @property
    def harga_standard_girik(self) -> Decimal | None:
        return getattr(getattr(self, 'tahap', 0), 'harga_standard_girik', 0)
    
    @property
    def harga_standard_sertifikat(self) -> Decimal | None:
        return getattr(getattr(self, 'tahap', 0), 'harga_standard_sertifikat', 0)
    
    @property
    def project_id(self) -> UUID | None:
        return getattr(getattr(self, 'tahap', None), 'project_id', None)
    
    @property
    def project_name(self) -> str | None:
        return getattr(getattr(self, 'tahap', None), 'project_name', None)
    
    @property
    def desa_name(self) -> str | None:
        return getattr(getattr(self, 'tahap', None), 'desa_name', None)
    
    @property
    def ptsk_id(self) -> UUID | None:
        return getattr(getattr(self, 'tahap', None), 'ptsk_id', None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, 'tahap', None), 'ptsk_name', None)
    
    @property
    def group(self) -> str | None:
        return getattr(getattr(self, 'tahap', None), 'group', None)
    
    @property
    def kjb_hd_code(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'code', None)
    
    @property
    def kjb_hd_group(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'nama_group', None)
    
    @property
    def utj_amount(self) -> str | None:
        return getattr(getattr(self, 'kjb_hd', None), 'utj_amount', None)
    
    @property
    def notaris_name(self) -> str | None:
        return getattr(getattr(self, 'notaris', None), 'name', None)

    @property
    def manager_name(self) -> str | None:
        return getattr(getattr(self, 'manager', None), 'name', None)
    
    @property
    def sales_name(self) -> str | None:
        return getattr(getattr(self, 'sales', None), 'name', None)
    
    @property
    def total_amount(self) -> Optional[Decimal]:
        array_total = [invoice.amount for invoice in self.invoices if invoice.is_void != True]
        total = sum(array_total)
        return total
    
    @property
    def step_name_workflow(self) -> str | None:
        return None
    
    @property
    def status_workflow(self) -> str | None:
        return None
    
    # @property
    # def last_status_at(self) -> datetime | None:
    #     return None
    
    # @declared_attr
    # def step_name_workflow(self) -> column_property:
    #     return column_property(
    #         select(
    #             Workflow.step_name
    #         )
    #         .select_from(
    #             Workflow)
    #         .where(Workflow.reference_id == self.id)
    #         .scalar_subquery()
    #     )
    
    # @declared_attr
    # def status_workflow(self) -> column_property:
    #     return column_property(
    #         select(
    #             Workflow.last_status
    #         )
    #         .select_from(
    #             Workflow)
    #         .where(Workflow.reference_id == self.id)
    #         .scalar_subquery()
    #     )
    
    # @declared_attr
    # def last_status_at(self) -> column_property:
    #     return column_property(
    #         select(
    #             Workflow.last_status_at
    #         )
    #         .select_from(
    #             Workflow)
    #         .where(Workflow.reference_id == self.id)
    #         .scalar_subquery()
    #     )
    
class TerminBayarBase(SQLModel):
    name: str | None = Field(nullable=True)
    termin_id:UUID = Field(nullable=False, foreign_key="termin.id")
    payment_method:PaymentMethodEnum = Field(nullable=False)
    rekening_id:UUID | None = Field(nullable=True, foreign_key="rekening.id")
    amount:Decimal = Field(nullable=False, default=0)
    remark:str | None = Field(nullable=True)
    activity:ActivityEnum | None = Field(nullable=True)
    pay_to: str | None = Field(nullable=True)

class TerminBayarFullBase(BaseUUIDModel, TerminBayarBase):
    pass

class TerminBayar(TerminBayarFullBase, table=True):
    termin:"Termin" = Relationship(
        back_populates="termin_bayars",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    invoice_bayars:list["InvoiceBayar"] =  Relationship(
        back_populates="termin_bayar",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    rekening:"Rekening" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    termin_bayar_dts:list["TerminBayarDt"] = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    @property
    def nama_pemilik_rekening(self) -> str|None:
        return getattr(getattr(self, "rekening", ''), "nama_pemilik_rekening", '')
    
    @property
    def bank_rekening(self) -> str|None:
        return getattr(getattr(self, "rekening", ''), "bank_rekening", '')
    
    @property
    def nomor_rekening(self) -> str|None:
        return getattr(getattr(self, "rekening", ''), "nomor_rekening", '')
    
    @property
    def amountExt(self) -> str|None:
        return "{:,.0f}".format(self.amount or 0)


class TerminBayarDtBase(SQLModel):
    termin_bayar_id: UUID = Field(nullable=False, foreign_key="termin_bayar.id")
    beban_biaya_id: UUID = Field(nullable=False, foreign_key="beban_biaya.id")

class TerminBayarDtFullBase(TerminBayarDtBase, BaseUUIDModel):
    pass

class TerminBayarDt(TerminBayarDtFullBase, table=True):
    beban_biaya: "BebanBiaya" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    @property
    def beban_biaya_name(self) -> str | None:
        return self.beban_biaya.name
    

