from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import text, select
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from fastapi_async_sqlalchemy import db
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, create_response)
from common.rounder import RoundTwo
from decimal import Decimal
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.writer.excel import save_workbook
from datetime import date
from io import BytesIO
import crud

router = APIRouter()

@router.get("/tim-ukur")
async def report_tim_ukur(start_date:date, end_date:date):

    wb = Workbook()
    ws = wb.active

    ws.title =  "REPORT TIM UKUR"
    ws.firstHeader

    header_string = ["No", "No. Permintaan Ukur", "Tanggal Terima Berkas", "Mediator", "Group", "Desa", "Nama Pemilik Tanah", "Jenis Surat (GIRIK/SHM)", 
                    "Alas Hak", "Luas Surat (m2)", "Tanggal Pengukuran", "Penunjuk Batas", "Luas Ukur (m2)", "Surveyor", "Tanggal Kirim Ukur ke Analis", "Keterangan"]
    
    end_column = len(header_string)

    ws.cell(row=1, column=2, value="LAPORAN PENGUKURAN")
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=4)
    ws.cell(row=2, column=2, value=f"CUT OFF DATE {start_date} S/D {end_date}")
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=4)

    for idx, val in enumerate(header_string):
        ws.cell(row=3, column=idx + 1, value=val).font = Font(bold=True)
        if idx + 1 < 11:
            ws.cell(row=3, column=idx + 1, value=val).fill = PatternFill(start_color="00FFFF00", end_color="00FFFF00", fill_type="solid")
        else:
            ws.cell(row=3, column=idx + 1, value=val).fill = PatternFill(start_color="00C0C0C0", end_color="00C0C0C0", fill_type="solid")


    if start_date:
            query_start_date = "rpl.tanggal_terima_berkas >=" f"'{start_date}'"
    if end_date:
        query_end_date = " AND rpl.tanggal_terima_berkas <" f"'{end_date}'"

    query = f"""
            SELECT
            ROW_NUMBER() OVER (ORDER BY rpl.code) AS no,
            rpl.code as no_permintaan_ukur,
            rpl.tanggal_terima_berkas,
            hd.mediator,
            dt.group,
            d.name as desa_name,
            p.name as pemilik_name,
            dt.jenis_alashak,
            dt.alashak,
            dt.luas_surat_by_ttn as luas_surat,
            rpl.tanggal_pengukuran,
            rpl.penunjuk_batas,
            rpl.luas_ukur,
            rpl.surveyor,
            rpl.tanggal_kirim_ukur,
            ket.name as keterangan
            FROM request_peta_lokasi rpl
            INNER JOIN kjb_dt dt ON dt.id = rpl.kjb_dt_id
            INNER JOIN kjb_hd hd ON hd.id = dt.kjb_hd_id
            LEFT OUTER JOIN desa d ON d.id = dt.desa_by_ttn_id
            LEFT OUTER JOIN pemilik p ON p.id = dt.pemilik_id
            LEFT OUTER JOIN keterangan_req_petlok ket ON ket.id = rpl.keterangan_req_petlok_id
            WHERE {query_start_date} {query_end_date}
    """

    db_session = db.session
    response = await db_session.execute(query)
    result = response.all()

    x = 3
    for row_data in result:
        x += 1
        ws.cell(row=x, column=1, value=row_data[0])
        ws.cell(row=x, column=2, value=row_data[1])
        ws.cell(row=x, column=3, value=row_data[2])
        ws.cell(row=x, column=4, value=row_data[3])
        ws.cell(row=x, column=5, value=row_data[4])
        ws.cell(row=x, column=6, value=row_data[5])
        ws.cell(row=x, column=7, value=row_data[6])
        ws.cell(row=x, column=8, value=row_data[7])
        ws.cell(row=x, column=9, value=row_data[8])
        ws.cell(row=x, column=10, value=row_data[9])
        ws.cell(row=x, column=11, value=row_data[10])
        ws.cell(row=x, column=12, value=row_data[11])
        ws.cell(row=x, column=13, value=row_data[12])
        ws.cell(row=x, column=14, value=row_data[13])
        ws.cell(row=x, column=15, value=row_data[14])
        ws.cell(row=x, column=16, value=row_data[15])
    
    ws.cell(row=x + 2, column=2, value="CATATAN:")
    ws.merge_cells(start_row=x + 2, start_column=2, end_row=x + 2, end_column=end_column)
    ws.cell(row=x + 3, column=2, value="1. KOLOM B S/D J DIPEROLEH DARI TIM MARKETING (DARI REQUEST UKUR/PETA LOKASI)")
    ws.merge_cells(start_row=x + 3, start_column=2, end_row=x + 3, end_column=end_column)
    ws.cell(row=x + 4, column=2, value="2. KOLOM K S/D P DIISI OLEH ADMIN UKUR DI SISTEM, SETELAH MENERIMA HASIL UKUR")
    ws.merge_cells(start_row=x + 4, start_column=2, end_row=x + 4, end_column=end_column)
    ws.cell(row=x + 5, column=2, value="3. 'TANGGAL PENGUKURAN' ADALAH TANGGAL TIM UKUR MELAKUKAN PENGUKURAN DI LAPANGAN ")
    ws.merge_cells(start_row=x + 5, start_column=2, end_row=x + 5, end_column=end_column)
    ws.cell(row=x + 6, column=2, value="4. 'TANGGAL KIRIM UKUR KE ANALIS' ADALAH TANGGAL TIM UKUR MENGIRIMKAN HASIL UKUR KE ANALIS")
    ws.merge_cells(start_row=x + 6, start_column=2, end_row=x + 6, end_column=end_column)
    ws.cell(row=x + 7, column=2, value="5. 'KETERANGAN' DIISI DENGAN INFORMASI DARI TIM UKUR APABILA ADA KENDALA/PENDING SEPERTI : BELUM UKUR MENUNGGU INFO MEDIATOR, PENJUAL BELUM MENUNJUKKAN BIDANG, DLL")
    ws.merge_cells(start_row=x + 7, start_column=2, end_row=x + 7, end_column=end_column)
    ws.cell(row=x + 8, column=2, value="6. 'TANGGAL TERIMA BERKAS' ADALAH TANGGAL TIM UKUR MENERIMA BERKAS UKUR DARI MARKETING")
    ws.merge_cells(start_row=x + 8, start_column=2, end_row=x + 8, end_column=end_column)
    

    excel_data = BytesIO()

    # Simpan workbook ke objek BytesIO
    wb.save(excel_data)

    # Set posisi objek BytesIO ke awal
    excel_data.seek(0)
    

    return StreamingResponse(excel_data,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                             headers={"Content-Disposition": "attachment; filename=generated_excel.xlsx"})