from enum import Enum

class StatusEnum(str, Enum):
    Bebas = "Bebas"
    Belum_Bebas = "Belum_Bebas"
    Batal = "Batal"
    Lanjut = "Lanjut"
    Pending = "Pending"

class TipeProsesEnum(str, Enum):
    Standard = "Standard"
    Bintang = "Bintang"

class TipeBidangEnum(str, Enum):
    Rincik = "Rincik"
    Bidang = "Bidang"
    Overlap = "Overlap"

class CategoryEnum(str, Enum):
    Group_Besar = "Group_Besar"
    Group_Kecil = "Group_Kecil"
    Asset = "Asset"
    Overlap = "Overlap"
    Default = "Unknown"

    @classmethod
    def _missing_(cls, value):
         return cls.Default 

class JenisDokumenEnum(str, Enum):
    AJB = "AJB"
    Sertifikat = "Sertifikat"
    Tanah_Garapan = "Tanah_Garapan"
    Akta_Hibah = "Akta_Hibah"
    SPPT = "SPPT"
    Kutipan_Girik = "Kutipan_Girik"
    Default = "Unknown"

    @classmethod
    def _missing_(cls, value):
         return cls.Default 

class JenisAlashakEnum(str, Enum):
    Girik = "Girik"
    Sertifikat = "Sertifikat"

class KategoriPenjualEnum(str, Enum):
    Perorangan = "Perorangan"
    Waris = "Waris"
    PT = "PT"

class JenisBayarEnum(str, Enum):
    UTJ = "UTJ"
    DP = "DP"
    LUNAS = "LUNAS"

class PosisiBidangEnum(str, Enum):
    Pinggir_Jalan = "Pinggir_Jalan"
    Standard = "Standard"
    Overlap = "Overlap"

class SatuanBayarEnum(str, Enum):
    Percentage = "Percentage"
    Amount = "Amount"

class StatusValidEnum(str, Enum):
    Valid = "Valid"
    Tidak_Valid = "Tidak_Valid"

class StatusPetaLokasiEnum(str, Enum):
    Lanjut_Peta_Lokasi = "Lanjut_Peta_Lokasi"
    Tidak_Lanjut = "Tidak_Lanjut"
