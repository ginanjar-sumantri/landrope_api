
from sqlmodel import SQLModel
from uuid import UUID

class SearchMapObj(SQLModel):
    type:str | None
    project_id:UUID | None
    project_name:str | None
    desa_id:UUID | None
    desa_name:str | None
    ptsk_id:str | None
    ptsk_name:str | None
    bidang_id:str | None
    id_bidang:str | None
    alashak:str | None