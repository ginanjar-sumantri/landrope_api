
from sqlmodel import SQLModel
from uuid import UUID
from pydantic import condecimal
from decimal import Decimal

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
    id_bidang_lama:str|None
    pemilik_name:str|None
    group:str|None
    mediator:str|None
    luas:Decimal|None

class SummaryProject(SQLModel):
    project_id:UUID | None
    project_name:str | None
    luas:condecimal(decimal_places=2) | None
    jumlah_bidang:int | None

class SummaryStatus(SummaryProject):
    status:str | None

class SummaryKategori(SummaryProject):
    status:str | None
    kategori_name:str | None
    shm:condecimal(decimal_places=2) | None
    girik:condecimal(decimal_places=2) | None

class FishboneKategori(SQLModel):
    kategori_name:str | None
    total:condecimal(decimal_places=2) | None
    shm:condecimal(decimal_places=2) | None
    girik:condecimal(decimal_places=2) | None
    percentage:condecimal(decimal_places=2) | None

class FishboneStatus(SQLModel):
    status:str | None
    luas:condecimal(decimal_places=2) | None
    percentage:condecimal(decimal_places=2) | None
    categories:list[FishboneKategori] | None

class FishboneProject(SQLModel):
    project_id:UUID | None
    project_name:str | None
    luas:condecimal(decimal_places=2) | None
    luas_planing:Decimal | None
    jumlah_bidang:int | None
    status:list[FishboneStatus] | None


class ParamProject(SQLModel):
    project_ids:list[UUID]
    planing_ids:list[UUID]



