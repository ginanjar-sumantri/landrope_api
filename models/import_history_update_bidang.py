from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class ImportHistoryUpdateBidang(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True, nullable=False)
    bidang_id: UUID | None = Field(nullable=True)
    kjb_dt_id: UUID | None = Field(nullable=True)
    alashak: str | None = Field(nullable=True)
    jenis_surat_id: UUID | None = Field(nullable=True)
    jenis_alashak: str | None = Field(nullable=True)
    pemilik_id: UUID | None = Field(nullable=True)
    imported_at: datetime | None = Field(nullable=True)