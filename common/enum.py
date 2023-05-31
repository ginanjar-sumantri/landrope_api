from enum import Enum

class JenisSuratEnum(str, Enum):
    Girik = "Girik"
    Sertifikat = "Sertifikasi"

class KategoriPenjualEnum(str, Enum):
    Perorangan = "Perorangan"
    Waris = "Waris"
    PT = "PT"

class JenisBayar(str, Enum):
    UTJ = "UTJ"
    DP = "DP"
    LUNAS = "LUNAS"