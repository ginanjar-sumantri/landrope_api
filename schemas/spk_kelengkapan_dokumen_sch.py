from models.spk_model import SpkKelengkapanDokumenBase, SpkKelengkapanDokumenFullBase
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID


class SpkKelengkapanDokumenCreateSch(SpkKelengkapanDokumenBase):
    pass

class SpkKelengkapanDokumenCreateExtSch(SQLModel):
    bundle_dt_id:UUID | None
    tanggapan:str | None 
    order_number:int | None
    field_value:str | None
    key_value:str | None

class SpkKelengkapanDokumenSch(SpkKelengkapanDokumenFullBase):
    dokumen_name:str | None = Field(alias="dokumen_name")
    has_meta_data:bool | None = Field(alias="has_meta_data")
    file_path:str | None = Field(alias="file_path")
    is_exclude_printout:bool | None
    order_number:int | None

class SpkKelengkapanDokumenByIdSch(SpkKelengkapanDokumenFullBase):
    pass

@optional
class SpkKelengkapanDokumenUpdateSch(SpkKelengkapanDokumenBase):
    pass

@optional
class SpkKelengkapanDokumenUpdateExtSch(SpkKelengkapanDokumenBase):
    id:UUID | None
    field_value:str | None