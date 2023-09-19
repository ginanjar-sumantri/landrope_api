from enum import Enum

class StatusBidangEnum(str, Enum):
    Bebas = "Bebas"
    Belum_Bebas = "Belum_Bebas"
    Deal = "Deal"
    Batal = "Batal"
    Lanjut = "Lanjut"
    Pending = "Pending"

class StatusSKEnum(str, Enum):
    Sudah_Il = "SUDAH_IL"
    Belum_IL = "BELUM_IL"

class KategoriSKEnum(str, Enum):
    SK_Orang = "SK_Orang"
    SK_ASG = "SK_ASG"

class JenisBidangEnum(str, Enum):
    Bintang = "Bintang"
    Standard = "Standard"
    Overlap = "Overlap"

class TipeProsesEnum(str, Enum):
    Standard = "Standard"
    Bintang = "Bintang"
    Overlap = "Overlap"

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

class SatuanHargaEnum(str, Enum):
    PerMeter2 = "Per_Meter2"
    Lumpsum = "Lumpsum" 

class StatusPetaLokasiEnum(str, Enum):
    Lanjut_Peta_Lokasi = "Lanjut_Peta_Lokasi"
    Tidak_Lanjut = "Tidak_Lanjut"

class TaskStatusEnum(str, Enum):
    OnProgress = "OnProgress"
    Done = "Done"
    Done_With_Error = "Done_With_Error"
    Failed = "Failed"

class TipeOverlapEnum(str, Enum):
    BintangLanjut = "Bintang_Lanjut"
    BintangBatal = "Bintang_Batal"
    BidangStandard_SudahBebas = "Bidang_Standard_Sudah_Bebas"
    BidangStandard_BelumBebas = "Bidang_Standard_Belum_Bebas"
    SertifikatOrangLain = "Sertifikat_Orang_Lain"
    NIBOrangLain = "NIB_Orang_Lain"

class StatusHasilPetaLokasiEnum(str, Enum):
    Lanjut = "Lanjut"
    Batal = "Batal"

class HasilAnalisaPetaLokasiEnum(str, Enum):
    Clear = "Clear"
    Overlap = "Overlap"

class ProsesBPNOrderGambarUkurEnum(str, Enum):
    PBT_Perorangan = "PBT_Perorangan"
    PBT_PT = "PBT_PT"

class TipeSuratGambarUkurEnum(str, Enum):
    Surat_Order = "Surat_Order"
    Surat_Tugas = "Surat_Tugas"

class StatusLuasOverlapEnum(str, Enum):
    Menambah_Luas = "Menambah_Luas"
    Tidak_Menambah_Luas = "Tidak_Menambah_Luas"

class TanggunganBiayaEnum(str, Enum):
    Pembeli = "Pembeli"
    Penjual = "Penjual"
    Penjual_Dibayar_Pembeli = "Penjual_Dibayar_Pembeli"
    
