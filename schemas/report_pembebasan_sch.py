from sqlmodel import SQLModel
from uuid import UUID
from decimal import Decimal


class SummaryProjectSch(SQLModel):
    section_id: UUID | None = None
    section_name: str | None = None
    id: UUID | None = None
    project_name: str | None = None
    kulit: Decimal | None = None
    total_target_bebas: Decimal | None = None
    bebas: Decimal | None = None
    deal_reklamasi: Decimal | None = None
    deal: Decimal | None = None
    belum_petlok: Decimal | None = None
    relokasi: Decimal | None = None
    kjb: Decimal | None = None
    total_bebas: Decimal | None = None
    belum_bebas: Decimal | None = None

class DetailProjectSch(SQLModel):
    id: UUID | None = None 
    jenis_bidang: str | None = None 
    project_id: UUID | None = None 
    desa_id: UUID | None = None 
    id_bidang: str | None = None 
    notaris_name: str | None = None 
    project_name: str | None = None 
    desa_name: str | None = None 
    group: str | None = None 
    manager_name: str | None = None 
    sales_name: str | None = None 
    pemilik_name: str | None = None
    mediator: str | None = None 
    jenis_alashak: str | None = None 
    alashak: str | None = None
    luas_surat: Decimal | None = None 
    luas_bayar: Decimal | None = None 
    kategori_name: str | None = None