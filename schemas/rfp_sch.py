from sqlmodel import SQLModel, Field
from uuid import UUID

class RfpCreateResponseSch(SQLModel):
    client_ref_no: str = Field(alias='client_ref_no')
    id: UUID | str = Field(alias='id')
    last_status: str | None = Field(alias='status')