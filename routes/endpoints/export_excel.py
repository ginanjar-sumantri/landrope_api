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
    # Membuat data Rumah dan Pembayaran
    data_rumah_list = [
        Rumah(
            id=1,
            luas=100,
            harga=200000,
            kepemilikan=[Kepemilikan(nama='Agus', tahun='2001'), Kepemilikan(nama='Ahmad', tahun='2010')],
            pembayaran=[Pembayaran(id=1, rumah_id=1, tanggal_pembayaran='2023-01-02', jenis_pembayaran='DP', jumlah=50000),
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

    # Membuat HTML dari data Rumah dan Pembayaran
    html_content = "<html><body>"
    html_content += "<table border='1'><tr><th>ID Rumah</th><th>Luas</th><th>Harga</th><th>nama</th><th>tahun</th>"
    
    # Menambahkan kolom pembayaran
    all_payment_types = []
    for rumah in data_rumah_list:
        for pembayaran in rumah.pembayaran:
            exists = next((types for types in all_payment_types if types['jenis_bayar'] == pembayaran.jenis_pembayaran and types['tanggal'] == pembayaran.tanggal_pembayaran), None)
            if exists:
                continue
            all_payment_types.append({'jenis_bayar':pembayaran.jenis_pembayaran, 'tanggal':pembayaran.tanggal_pembayaran})
    for payment_type in all_payment_types:
        html_content += f"<th colspan='3'>{payment_type['jenis_bayar']} {payment_type['tanggal']}</th>"
    html_content += "</tr>"

    for rumah in data_rumah_list:
        html_content += f"<tr><td rowspan='{len(rumah.kepemilikan) + 1}'>{rumah.id}</td><td rowspan='{len(rumah.kepemilikan) + 1}'>{rumah.luas}</td><td rowspan='{len(rumah.kepemilikan) + 1}'>{rumah.harga}</td>"
        
        # Menambahkan data Kepemilikan
        for i, kepemilikan in enumerate(rumah.kepemilikan):
            if i == 0:
                html_content += f"<td>{kepemilikan.nama}</td><td>{kepemilikan.tahun}</td></tr>"
            else:
                html_content += f"<tr><td>{kepemilikan.nama}</td><td>{kepemilikan.tahun}</td></tr>"
        
        # Menambahkan data Pembayaran
        if rumah.pembayaran:
            for payment_type in all_payment_types:
                matching_payment = next((p for p in rumah.pembayaran if p.jenis_pembayaran == payment_type['jenis_bayar'] and p.tanggal_pembayaran == payment_type['tanggal']), None)
                if matching_payment:
                    html_content += f"<td rowspan='{len(rumah.kepemilikan) + 1}'>{matching_payment.jumlah}</td>"
                else:
                    html_content += "<td rowspan='{len(rumah.kepemilikan) + 1}'></td>"
        else:
            for payment_type in all_payment_types:
                html_content += "<td rowspan='{len(rumah.kepemilikan) + 1}'></td>"
        html_content += "</tr>"
        
        # # Menambahkan data Pembayaran
        # if rumah.pembayaran:
        #     for payment_type in all_payment_types:
        #         matching_payments = [p for p in rumah.pembayaran if p.jenis_pembayaran == payment_type]
        #         if matching_payments:
        #             html_content += "<tr>"
        #             for payment in matching_payments:
        #                 html_content += f"<td>{payment.tanggal_pembayaran}</td><td>{payment.jenis_pembayaran}</td><td>{payment.jumlah}</td>"
        #             html_content += "</tr>"
        #         else:
        #             html_content += "<tr><td></td><td></td><td></td></tr>"
        # else:
        #     for payment_type in all_payment_types:
        #         html_content += "<tr><td></td><td></td><td></td></tr>"

    html_content += "</table></body></html>"

    try:
        df = pd.read_html(html_content)[0]

        excel_output = BytesIO()
        df.to_excel(excel_output, index=False)
        
        excel_output.seek(0)

        return StreamingResponse(BytesIO(excel_output.getvalue()), 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=memo_data.xlsx"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
