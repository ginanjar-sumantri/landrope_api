from enum import Enum
from models.code_counter_model import CodeCounterEnum

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
    Rincik = "Rincik"
    Bintang = "Bintang"
    Standard = "Standard"
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
    UTJ_KHUSUS = "UTJ_KHUSUS"
    DP = "DP"
    LUNAS = "LUNAS"
    PELUNASAN = "PELUNASAN"
    PAJAK = "PAJAK"
    PENGEMBALIAN_BEBAN_PENJUAL = "PENGEMBALIAN_BEBAN_PENJUAL"
    BEGINNING_BALANCE = "BEGINNING_BALANCE"
    BIAYA_LAIN = "BIAYA_LAIN"
    SISA_PELUNASAN = "SISA_PELUNASAN"
    TAMBAHAN_DP = "TAMBAHAN_DP"

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

class PaymentMethodEnum(str, Enum):
    Giro = "Giro"
    Cek = "Cek"
    Tunai = "Tunai"

class KategoriOverlapEnum(str, Enum):
    A = "A" #alashak
    B = "B" #PBT/NIB
    C = "C" #pengumuman
    D = "D" #SHM
    
class WorkflowLastStatusEnum(str, Enum):
    ISSUED = "ISSUED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    NEED_DATA_UPDATE = "NEED_DATA_UPDATE"
    WAITING_APPROVAL = "WAITING_APPROVAL"

class WorkflowEntityEnum(str, Enum):
    SPK = "SPK"
    TERMIN = "TERMIN"
    KJB = "KJB"

class StatusPembebasanEnum(str, Enum):
    INPUT_PETA_LOKASI = "INPUT_PETA_LOKASI"
    SPK_DP = "SPK_DP"
    SPK_LUNAS = "SPK_LUNAS"
    SPK_PELUNASAN = "SPK_PELUNASAN"
    PEMBAYARAN_DP = "PEMBAYARAN_DP"
    PEMBAYARAN_LUNAS = "PEMBAYARAN_LUNAS"
    PEMBAYARAN_PELUNASAN = "PEMBAYARAN_PELUNASAN"

class PaymentStatusEnum(str, Enum):
    BUKA_GIRO = "BUKA_GIRO"
    CAIR_GIRO = "CAIR_GIRO"

jenis_bayar_to_text = {
    JenisBayarEnum.UTJ : "UTJ",
    JenisBayarEnum.UTJ_KHUSUS : "UTJ",
    JenisBayarEnum.DP : "DP",
    JenisBayarEnum.LUNAS : "LUNAS",
    JenisBayarEnum.PELUNASAN : "PELUNASAN",
    JenisBayarEnum.PAJAK : "PAJAK",
    JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL : "PENGEMBALIAN",
    JenisBayarEnum.BEGINNING_BALANCE : "BEGINNING-BALANCE",
    JenisBayarEnum.BIAYA_LAIN : "BIAYA-LAIN",
    JenisBayarEnum.SISA_PELUNASAN : "KURANG-BAYAR",
    JenisBayarEnum.TAMBAHAN_DP : "TAMBAHAN-DP"
}

jenis_bayar_to_code_counter_enum = {
    JenisBayarEnum.UTJ : CodeCounterEnum.Utj,
    JenisBayarEnum.UTJ_KHUSUS : CodeCounterEnum.Utj,
    JenisBayarEnum.DP : CodeCounterEnum.Dp,
    JenisBayarEnum.LUNAS : CodeCounterEnum.Lunas,
    JenisBayarEnum.PELUNASAN : CodeCounterEnum.Pelunasan,
    JenisBayarEnum.PAJAK : None,
    JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL : CodeCounterEnum.Pengembalian_Beban_Penjual,
    JenisBayarEnum.BEGINNING_BALANCE : None,
    JenisBayarEnum.BIAYA_LAIN : CodeCounterEnum.Biaya_Lain,
    JenisBayarEnum.SISA_PELUNASAN : CodeCounterEnum.Sisa_Pelunasan,
    JenisBayarEnum.TAMBAHAN_DP : CodeCounterEnum.Tambahan_Dp
}

jenis_bayar_to_spk_status_pembebasan = {
    JenisBayarEnum.DP : StatusPembebasanEnum.SPK_DP,
    JenisBayarEnum.PELUNASAN : StatusPembebasanEnum.SPK_PELUNASAN,
    JenisBayarEnum.LUNAS : StatusPembebasanEnum.SPK_LUNAS
}

jenis_bayar_to_termin_status_pembebasan_dict = {
    JenisBayarEnum.DP : StatusPembebasanEnum.PEMBAYARAN_DP,
    JenisBayarEnum.PELUNASAN : StatusPembebasanEnum.PEMBAYARAN_PELUNASAN,
    JenisBayarEnum.LUNAS : StatusPembebasanEnum.PEMBAYARAN_LUNAS
}