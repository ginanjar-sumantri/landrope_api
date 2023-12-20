from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
from typing import List
from pydantic import BaseModel

router = APIRouter()

# Data class model
class Kepemilikan(BaseModel):
    nama: str
    tahun: str

class Pembayaran(BaseModel):
    id: int
    rumah_id: int
    tanggal_pembayaran: str
    jenis_pembayaran: str
    jumlah: int

class Rumah(BaseModel):
    id: int
    luas: int
    harga: int
    kepemilikan: List[Kepemilikan]
    pembayaran: List[Pembayaran]



# API endpoint to get the data in Excel format
@router.get("/export_excel")
async def export_excel():
    # Data example
    data_rumah_list = [
    Rumah(
        id=1,
        luas=100,
        harga=200000,
        kepemilikan=[Kepemilikan(nama='Agus', tahun='2001'), Kepemilikan(nama='Ahmad', tahun='2010')],
        pembayaran=[Pembayaran(id=1, rumah_id=1, tanggal_pembayaran='2023-01-01', jenis_pembayaran='DP', jumlah=50000),
                    Pembayaran(id=2, rumah_id=1, tanggal_pembayaran='2023-01-02', jenis_pembayaran='LUNAS', jumlah=180000)]
    ),
    Rumah(
        id=2,
        luas=120,
        harga=250000,
        kepemilikan=[Kepemilikan(nama='Budi', tahun='2005'), Kepemilikan(nama='Cindy', tahun='2012')],
        pembayaran=[Pembayaran(id=3, rumah_id=2, tanggal_pembayaran='2023-01-02', jenis_pembayaran='DP', jumlah=150000),
                    Pembayaran(id=4, rumah_id=2, tanggal_pembayaran='2023-01-04', jenis_pembayaran='DP', jumlah=200000)]
    ),
    # Rumah-rumah tambahan tanpa pembayaran
    Rumah(
        id=3,
        luas=80,
        harga=180000,
        kepemilikan=[Kepemilikan(nama='David', tahun='2003')],
        pembayaran=[]  # Tidak ada pembayaran untuk rumah ini
    ),
    Rumah(
        id=4,
        luas=150,
        harga=300000,
        kepemilikan=[Kepemilikan(nama='Eva', tahun='2011')],
        pembayaran=[]  # Tidak ada pembayaran untuk rumah ini
    ),
]

    # Buat DataFrame kosong untuk menyimpan hasil
    df_final = pd.DataFrame()

    # Loop melalui setiap rumah dan pembayaran
    for rumah in data_rumah_list:
        # Tambahkan informasi rumah ke DataFrame akhir
        df_rumah = pd.DataFrame([rumah.dict()])
        df_final = pd.concat([df_final, df_rumah], ignore_index=True)

        # Jika terdapat riwayat kepemilikan untuk rumah tersebut
        if rumah.kepemilikan:
            # Buat DataFrame untuk riwayat kepemilikan
            df_kepemilikan = pd.DataFrame([{
                'Kepemilikan_{}_{}'.format(i + 1, key): value
                for key, value in kepemilikan.dict().items()
            } for i, kepemilikan in enumerate(rumah.kepemilikan)])

            # Tambahkan kolom 'rumah_id' sebagai indeks untuk setiap baris
            df_kepemilikan['rumah_id'] = rumah.id

            # Gabungkan informasi riwayat kepemilikan ke DataFrame akhir
            df_final = pd.concat([df_final, df_kepemilikan], ignore_index=True)

    # Ganti NaN dengan string kosong
    df_final = df_final.fillna('')

    # Lakukan pivot untuk data pembayaran
    df_pembayaran = pd.DataFrame()
    for jenis_pembayaran in df_final['jenis_pembayaran'].unique():
        df_pembayaran_jenis = df_final[df_final['jenis_pembayaran'] == jenis_pembayaran][['rumah_id', 'tanggal_pembayaran', 'jumlah']]
        df_pembayaran_jenis = df_pembayaran_jenis.pivot(index='rumah_id', columns='tanggal_pembayaran', values='jumlah')
        df_pembayaran_jenis.columns = ['{}_{}'.format(jenis_pembayaran, col) for col in df_pembayaran_jenis.columns]
        df_pembayaran = pd.concat([df_pembayaran, df_pembayaran_jenis], axis=1, ignore_index=True)

    # Ganti NaN dengan string kosong
    df_pembayaran = df_pembayaran.fillna('')

    # Gabungkan DataFrame pembayaran ke DataFrame akhir
    df_final = pd.concat([df_final, df_pembayaran], axis=1, ignore_index=True)

    # Hapus kolom yang tidak diperlukan
    df_final = df_final.drop(['kepemilikan', 'pembayaran'], axis=1)

    # Simpan DataFrame ke file Excel
    excel_output = BytesIO()
    df_final.to_excel(excel_output, index=False, merge_cells=False)

    try:
        excel_output.seek(0)

        return StreamingResponse(BytesIO(excel_output.getvalue()), 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=memo_data.xlsx"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
