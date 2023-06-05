from enum import Enum

class JenisAlashakEnum(str, Enum):
    Girik = "Girik"
    Sertifikat = "Sertifikasi"

class KategoriPenjualEnum(str, Enum):
    Perorangan = "Perorangan"
    Waris = "Waris"
    PT = "PT"

class JenisBayarEnum(str, Enum):
    UTJ = "UTJ"
    DP = "DP"
    LUNAS = "LUNAS"