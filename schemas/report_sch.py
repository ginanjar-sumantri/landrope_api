from sqlmodel import SQLModel
from uuid import UUID
from decimal import Decimal

class KekuranganBerkasManagerSch(SQLModel):
    manager_id:UUID|None
    manager_name:str|None
    desa_name:str|None
    nama_penjual:str|None
    alashak:str|None
    luas_m2:Decimal|None
    luas_ha:Decimal|None
    ktp_penjual:str|None
    ktp_pasangan:str|None
    kk:str|None
    surat_nikah:str|None
    ktp_pengurus:str|None
    ad_art:str|None
    perubahan_ad_art:str|None
    surat_akta_kematian:str|None
    surat_ket_ahli_waris:str|None
    surat_kuasa_waris:str|None
    ktp_seluruh_Waris:str|None
    kk_seluruh_waris:str|None