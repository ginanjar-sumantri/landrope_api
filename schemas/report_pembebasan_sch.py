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