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
from openpyxl.styles import Font
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
    
    for idx, val in enumerate(header_string):
        ws.cell(row=1, column=idx + 1, value=val).font = Font(bold=True)

    if start_date:
            query_start_date = "rpl.tanggal_terima_berkas >="f'"{start_date}"'
    if end_date:
        query_end_date = " AND rpl.tanggal_terima_berkas < "f'"{end_date}"'

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
            --WHERE ({query_start_date} {query_end_date})
    """

    db_session = db.session
    response = await db_session.execute(query)
    result = response.all()

    x = 1
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

    excel_data = BytesIO()

    # Simpan workbook ke objek BytesIO
    wb.save(excel_data)

    # Set posisi objek BytesIO ke awal
    excel_data.seek(0)
    

    return StreamingResponse(excel_data,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                             headers={"Content-Disposition": "attachment; filename=generated_excel.xlsx"})