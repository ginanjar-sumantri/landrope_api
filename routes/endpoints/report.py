from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import text, select, SQLModel, update
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from fastapi_async_sqlalchemy import db
from models import HasilPetaLokasi
from schemas.hasil_peta_lokasi_sch import HasiLPetaLokasiUpdateTanggalKirimBerkasSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, create_response)
from common.rounder import RoundTwo
from decimal import Decimal
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.writer.excel import save_workbook
from datetime import date
from io import BytesIO
import crud

router = APIRouter()

@router.get("/tim-ukur")
async def report_tim_ukur(start_date:date | None = None, end_date:date|None = None):

    wb = Workbook()
    ws = wb.active

    ws.title =  "REPORT TIM UKUR"
    ws.firstHeader

    ws.cell(row=1, column=2, value="LAPORAN PENGUKURAN")
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=4)
    ws.cell(row=2, column=2, value=f"CUT OFF DATE {start_date} S/D {end_date}")
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=4)

    header_string = ["No", "No. Permintaan Ukur", "Tanggal Terima Berkas", "Mediator", "Group", "Desa", "Nama Pemilik Tanah", "Jenis Surat (GIRIK/SHM)", 
                    "Alas Hak", "Luas Surat (m2)", "Tanggal Pengukuran", "Penunjuk Batas", "Luas Ukur (m2)", "Surveyor", "Tanggal Kirim Ukur ke Analis", "Keterangan"]
    
    end_column = len(header_string)

    for idx, val in enumerate(header_string):
        ws.cell(row=3, column=idx + 1, value=val).font = Font(bold=True)
        if idx + 1 < 11:
            ws.cell(row=3, column=idx + 1, value=val).fill = PatternFill(start_color="00FFFF00", end_color="00FFFF00", fill_type="solid")
        else:
            ws.cell(row=3, column=idx + 1, value=val).fill = PatternFill(start_color="00C0C0C0", end_color="00C0C0C0", fill_type="solid")

    query_start_date = ""
    if start_date and end_date:
        query_start_date = "WHERE rpl.tanggal_terima_berkas >=" f"'{start_date}'"
        query_start_date += " AND rpl.tanggal_terima_berkas <" f"'{end_date}'"

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
            dt.luas_surat as luas_surat,
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
            {query_start_date}
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

@router.get("/tim-analyst")
async def report_tim_analyst(start_date:date | None = None, end_date:date|None = None):

    wb = Workbook()
    ws = wb.active

    ws.title =  "REPORT TIM ANALYST"
    ws.firstHeader

    ws.cell(row=1, column=2, value="LAPORAN ANALISA PETA LOKASI")
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=4)
    ws.cell(row=2, column=2, value=f"CUT OFF DATE {start_date} S/D {end_date}")
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=4)

    header_string = ["No", "No. Permintaan Ukur", "Tanggal Serah Terima Ukur", "Mediator", "Group", "Nama Pemilik Tanah", "Jenis Surat", "Alas Hak", "Luas (m2)", 
                    "Desa", "Project", "PT SK", "Nama Petugas Analyst", "No. ID Bidang", "L SURAT", "L UKUR", "L NETT", "L CLEAR", "L OVERLAP", "ID OVERLAP", 
                    "Ket (Overlap/Clear)", "L Proses (PBT dan SERTIFIKASI)", "Tanggal Serah Terima ke Tim Marketing", "Selisih Hari"]
    
    end_column = len(header_string)

    for idx, val in enumerate(header_string):
        ws.cell(row=3, column=idx + 1, value=val).font = Font(bold=True)
        if idx + 1 < 10:
            ws.cell(row=3, column=idx + 1, value=val).fill = PatternFill(start_color="00C0C0C0", end_color="00C0C0C0", fill_type="solid")
        else: 
            ws.cell(row=3, column=idx + 1, value=val).fill = PatternFill(start_color="00FFFF00", end_color="00FFFF00", fill_type="solid")
            

    query_start_date = ""
    if start_date and end_date:
        query_start_date = "WHERE rpl.tanggal_terima_berkas >=" f"'{start_date}'"
        query_start_date += " AND rpl.tanggal_terima_berkas <" f"'{end_date}'"

    query = f"""
            SELECT
            ROW_NUMBER() OVER (ORDER BY rpl.code) AS no,
            rpl.code as no_permintaan_ukur,
            rpl.tanggal_kirim_ukur,
            hd.mediator,
            dt.group,
            p.name as pemilik_name,
            dt.jenis_alashak,
            dt.alashak,
            dt.luas_surat as luas_surat,
            d.name as desa_name,
            pr.name as project_name,
            pt.name as ptsk_name,
            w.name as petugas_name,
            b.id_bidang as no_id_bidang,
            hpl.luas_surat,
            hpl.luas_ukur,
            hpl.luas_nett,
            hpl.luas_clear,
            bo.luas as luas_overlap,
            bd.id_bidang as id_overlap,
            hpl.hasil_analisa_peta_lokasi,
            hpl.luas_proses,
            hpl.tanggal_kirim_berkas,
            Coalesce((hpl.tanggal_kirim_berkas - rpl.tanggal_terima_berkas), 0) as selisih
            FROM hasil_peta_lokasi_detail hpl_dt
            INNER JOIN bidang_overlap bo ON bo.id = hpl_dt.bidang_overlap_id
            INNER JOIN hasil_peta_lokasi hpl ON hpl.id = hpl_dt.hasil_peta_lokasi_id
            INNER JOIN request_peta_lokasi rpl ON rpl.id = hpl.request_peta_lokasi_id
            INNER JOIN kjb_dt dt ON dt.id = rpl.kjb_dt_id
            INNER JOIN kjb_hd hd ON hd.id = dt.kjb_hd_id
            LEFT OUTER JOIN pemilik p ON p.id = dt.pemilik_id
            LEFT OUTER JOIN planing pl ON pl.id = hpl.planing_id
            LEFT OUTER JOIN desa d ON d.id = pl.desa_id
            LEFT OUTER JOIN project pr ON pr.id = pl.project_id
            LEFT OUTER JOIN skpt sk ON sk.id = hpl.skpt_id
            LEFT OUTER JOIN ptsk pt ON pt.id = sk.ptsk_id
            INNER JOIN worker w ON w.id = hpl.created_by_id
            INNER JOIN bidang b ON b.id = hpl.bidang_id
            INNER JOIN bidang bd ON bd.id = bo.parent_bidang_intersect_id
            {query_start_date}
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
        ws.cell(row=x, column=17, value=row_data[16])
        ws.cell(row=x, column=18, value=row_data[17])
        ws.cell(row=x, column=19, value=row_data[18])
        ws.cell(row=x, column=20, value=row_data[19])
        ws.cell(row=x, column=21, value=row_data[20])
        ws.cell(row=x, column=22, value=row_data[21])
        ws.cell(row=x, column=23, value=row_data[22])
        ws.cell(row=x, column=24, value=row_data[23])
    
    ws.cell(row=x + 2, column=2, value="CATATAN:")
    ws.merge_cells(start_row=x + 2, start_column=2, end_row=x + 2, end_column=end_column)
    ws.cell(row=x + 3, column=2, value="LUAS NETT: LUAS UKUR YANG DIKURANGI DENGAN OVERLAP BID LAIN NON BINTANG SEPERTI: OVERLAP SHM, DAN OVERLAP TANAH MILIK PT")
    ws.merge_cells(start_row=x + 3, start_column=2, end_row=x + 3, end_column=end_column)
    ws.cell(row=x + 4, column=2, value="LUAS SURAT ADALAH LUAS YANG DIDAPAT DARI ALAS HAK YANG DITERIMA. SUDAH DIINPUT OLEH TIM MARKETING DARI MODUL PRA-PEMBEBASAN")
    ws.merge_cells(start_row=x + 4, start_column=2, end_row=x + 4, end_column=end_column)
    ws.cell(row=x + 5, column=2, value="LUAS UKUR ADALAH LUAS HASIL UKUR FISIK LAPANGAN")
    ws.merge_cells(start_row=x + 5, start_column=2, end_row=x + 5, end_column=end_column)
    ws.cell(row=x + 6, column=2, value="LUAS SURAT BISA BERUBAH, KASUSNYA LUAS FISIK JAUH LEBIH BESAR DARI LUAS SURAT SEHINGGA")
    ws.merge_cells(start_row=x + 6, start_column=2, end_row=x + 6, end_column=end_column)
    ws.cell(row=x + 7, column=2, value="ADA MODUL UNTUK REVISI LUAS SURAT DI TIM PRA PEMBEBASAN, ADA PILIHAN UNTUK RENVOY SURAT")
    ws.merge_cells(start_row=x + 7, start_column=2, end_row=x + 7, end_column=end_column)

    excel_data = BytesIO()

    # Simpan workbook ke objek BytesIO
    wb.save(excel_data)

    # Set posisi objek BytesIO ke awal
    excel_data.seek(0)
    

    return StreamingResponse(excel_data,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                             headers={"Content-Disposition": "attachment; filename=generated_excel.xlsx"})

class HasilAnalisa(SQLModel):
     ids:list[UUID]|None

@router.post("/hasil-analisa")
async def report_hasil_analisa(background_task:BackgroundTasks, sch:HasiLPetaLokasiUpdateTanggalKirimBerkasSch|None = None):
    
    ids = [f"'{str(req)}'" for req in sch.ids]
    ids_str = ",".join(ids)
    
    wb = Workbook()
    ws = wb.active

    ws.title =  "REPORT HASIL ANALISA"
    ws.firstHeader

    ws.cell(row=1, column=2, value="HASIL ANALISA")
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=4)
    ws.cell(row=2, column=2, value=f"NO: {sch.code}")
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=4)

    header_string = ["No", "Mediator", "Group", "Nama Pemilik Tanah", "No. Telp Pemilik Tanah", "Alas Hak", "Luas (m2)", 
                    "Desa", "Project", "PT", "Nama Petugas Analyst", "No. Id Bidang", "Luas (m2)", "Ket (Overlap/Clear)"]

    for idx, val in enumerate(header_string):
        ws.cell(row=4, column=idx + 1, value=val).font = Font(bold=True)
        ws.cell(row=4, column=idx + 1, value=val).fill = PatternFill(start_color="00C0C0C0", end_color="00C0C0C0", fill_type="solid")


    query = f"""
            SELECT 
            ROW_NUMBER() OVER (ORDER BY hpl.id) AS no,
            hd.mediator,
            dt.group,
            p.name as pemilik_name,
            (select nomor_telepon from kontak k where k.pemilik_id = p.id limit 1) as no_pemilik,
            dt.alashak,
            dt.luas_surat_by_ttn as luas_surat,
            d.name as desa_name,
            pr.name as project_name,
            pt.name as ptsk_name,
            w.name as petugas_name,
            b.id_bidang,
            hpl.luas_ukur,
            hpl.hasil_analisa_peta_lokasi
            FROM hasil_peta_lokasi hpl
            INNER JOIN kjb_dt dt ON dt.id = hpl.kjb_dt_id 
            INNER JOIN kjb_hd hd ON hd.id = dt.kjb_hd_id
            INNER JOIN pemilik p ON p.id = hpl.pemilik_id
            LEFT OUTER JOIN planing pl ON pl.id = hpl.planing_id
            LEFT OUTER JOIN desa d ON d.id = pl.desa_id
            LEFT OUTER JOIN project pr ON pr.id = pl.project_id
            LEFT OUTER JOIN skpt sk ON sk.id = hpl.skpt_id
            LEFT OUTER JOIN ptsk pt ON pt.id = sk.ptsk_id
            INNER JOIN worker w ON w.id = hpl.created_by_id
            INNER JOIN bidang b ON b.id = hpl.bidang_id
            WHERE hpl.id IN ({ids_str})
    """

    db_session = db.session
    response = await db_session.execute(query)
    result = response.all()

    x = 4
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

    excel_data = BytesIO()

    # Simpan workbook ke objek BytesIO
    wb.save(excel_data)

    # Set posisi objek BytesIO ke awal
    excel_data.seek(0)

    background_task.add_task(update_tanggal_kirim_berkas, sch)

    return StreamingResponse(excel_data,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                             headers={"Content-Disposition": "attachment; filename=generated_excel.xlsx"})


async def update_tanggal_kirim_berkas(sch:HasiLPetaLokasiUpdateTanggalKirimBerkasSch):
     
    query = update(HasilPetaLokasi).where(HasilPetaLokasi.id.in_(sch.ids)).values(tanggal_kirim_berkas=sch.tanggal_kirim_berkas)
    
    db_session = db.session
    await db_session.execute(query)
    await db_session.commit()


@router.get("/summary-analyst")
async def report_summary_analyst(start_date:date, end_date:date):

    wb = Workbook()
    ws = wb.active

    ws.title =  "REPORT TIM UKUR"
    ws.firstHeader

    ws.cell(row=1, column=2, value="LAPORAN PENGUKURAN")
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=6)
    ws.cell(row=2, column=2, value=f"CUT OFF DATE {start_date} S/D {end_date}")
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=6)

    ws.cell(row=3, column=8, value="Laporan Ukuran")
    ws.cell(row=3, column=8, value="Laporan Ukuran").font = Font(bold=True)
    ws.cell(row=3, column=8, value="Laporan Ukuran").fill = PatternFill(start_color="00C0C0C0", end_color="00C0C0C0", fill_type="solid")
    ws.cell(row=3, column=8, value="Laporan Ukuran").alignment = Alignment(horizontal='center', vertical='center')
    ws.merge_cells(start_row=3, start_column=8, end_row=3, end_column=11)

    ws.cell(row=3, column=12, value=f"Laporan Analis")
    ws.cell(row=3, column=12, value="Laporan Analis").font = Font(bold=True)
    ws.cell(row=3, column=12, value="Laporan Analis").fill = PatternFill(start_color="00C0C0C0", end_color="00C0C0C0", fill_type="solid")
    ws.cell(row=3, column=12, value="Laporan Analis").alignment = Alignment(horizontal='center', vertical='center')
    ws.merge_cells(start_row=3, start_column=12, end_row=3, end_column=15)

    r4c8 = ws.cell(row=4, column=8)
    r4c8.font = Font(bold=True)
    r4c8.fill = PatternFill(start_color="0099CC00", end_color="0099CC00", fill_type="solid")
    r4c8.alignment = Alignment(horizontal='center', vertical='center')
    r4c8.value = "Sudah Ukur"
    ws.merge_cells(start_row=4, start_column=8, end_row=4, end_column=9)

    r4c10 = ws.cell(row=4, column=10)
    r4c10.font = Font(bold=True)
    r4c10.fill = PatternFill(start_color="00993366", end_color="00993366", fill_type="solid")
    r4c10.alignment = Alignment(horizontal='center', vertical='center')
    r4c10.value = "Belum Ukur"
    ws.merge_cells(start_row=4, start_column=10, end_row=4, end_column=11)

    r4c12 = ws.cell(row=4, column=12)
    r4c12.font = Font(bold=True)
    r4c12.fill = PatternFill(start_color="0099CC00", end_color="0099CC00", fill_type="solid")
    r4c12.alignment = Alignment(horizontal='center', vertical='center')
    r4c12.value = "Dibeli"
    ws.merge_cells(start_row=4, start_column=12, end_row=4, end_column=13)

    r4c14 = ws.cell(row=4, column=14)
    r4c14.font = Font(bold=True)
    r4c14.fill = PatternFill(start_color="00993366", end_color="00993366", fill_type="solid")
    r4c14.alignment = Alignment(horizontal='center', vertical='center')
    r4c14.value = "Tidak Dibeli"
    ws.merge_cells(start_row=4, start_column=14, end_row=4, end_column=15)

    header_string = ["Nomor KJB", "Desa", "Group", "Manager", "No Permintaan Ukur", "Jumlah Bidang", "Total Luas (m2)",
                    "Bidang", "Luas (m2)", "Bidang", "Luas (m2)", "Bidang", "Luas (m2)", "Bidang", "Luas (m2)", "Status"]
    
    end_column = len(header_string)

    for idx, val in enumerate(header_string):
        ws.cell(row=5, column=idx + 1, value=val).font = Font(bold=True)
        ws.cell(row=5, column=idx + 1, value=val).fill = PatternFill(start_color="00C0C0C0", end_color="00C0C0C0", fill_type="solid")

    query_start_date = ""
    if start_date and end_date:
        query_start_date = "WHERE rpl.tanggal_terima_berkas >=" f"'{start_date}'"
        query_start_date += " AND rpl.tanggal_terima_berkas <" f"'{end_date}'"

    query = f"""
            WITH subquery AS (SELECT
            hd.code AS nomor_kjb,
            d.name AS desa_name,
            dt.group,
            m.name AS manager_name,
            rpl.code AS nomor_request,
            COUNT(rpl.kjb_dt_id) AS jumlah_bidang,
            SUM(dt.luas_surat_by_ttn) AS total_luas,
            COALESCE((SELECT COUNT(rpl_.id) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            WHERE rpl_.code = rpl.code 
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')
            AND rpl_.luas_ukur IS NOT NULL 
            AND rpl_.tanggal_pengukuran IS NOT NULL), 0) AS sudah_diukur,
            COALESCE((SELECT SUM(rpl_.luas_ukur) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            WHERE rpl_.code = rpl.code 
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')
            AND rpl_.luas_ukur IS NOT NULL 
            AND rpl_.tanggal_pengukuran IS NOT NULL), 0) AS luas_sudah_diukur,
            COALESCE((SELECT COUNT(rpl_.id) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            WHERE rpl_.code = rpl.code
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')
            AND rpl_.luas_ukur IS NULL 
            AND rpl_.tanggal_pengukuran IS NULL), 0) AS belum_diukur,
            COALESCE((SELECT SUM(dt_.luas_surat_by_ttn) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            WHERE rpl_.code = rpl.code 
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')
            AND rpl_.luas_ukur IS NULL 
            AND rpl_.tanggal_pengukuran IS NULL), 0) AS luas_belum_diukur,
            COALESCE((SELECT COUNT(rpl_.id) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            INNER JOIN hasil_peta_lokasi hpl_ ON rpl_.id = hpl_.request_peta_lokasi_id
            WHERE rpl_.code = rpl.code 
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')), 0) AS dibeli,
            COALESCE((SELECT SUM(hpl_.luas_surat) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            INNER JOIN hasil_peta_lokasi hpl_ ON rpl_.id = hpl_.request_peta_lokasi_id
            WHERE rpl_.code = rpl.code 
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')), 0) AS luas_dibeli,
            COALESCE((SELECT COUNT(rpl_.id) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            LEFT OUTER JOIN hasil_peta_lokasi hpl_ ON rpl_.id = hpl_.request_peta_lokasi_id
            WHERE rpl_.code = rpl.code 
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')
            AND hpl_.id IS NULL), 0) AS tidak_dibeli,
            COALESCE((SELECT SUM(hpl_.luas_surat) 
            FROM request_peta_lokasi rpl_ 
            INNER JOIN kjb_dt dt_ ON dt_.id = rpl_.kjb_dt_id
            INNER JOIN hasil_peta_lokasi hpl_ ON rpl_.id = hpl_.request_peta_lokasi_id
            WHERE rpl_.code = rpl.code 
            AND d.id = dt_.desa_by_ttn_id 
            AND COALESCE(dt.group, '') = COALESCE(dt_.group, '')
            AND hpl_.id IS NULL), 0) AS luas_tidak_dibeli
            FROM request_peta_lokasi rpl
            INNER JOIN kjb_dt dt ON dt.id = rpl.kjb_dt_id
            INNER JOIN kjb_hd hd ON hd.id = dt.kjb_hd_id
            LEFT OUTER JOIN desa d ON d.id = dt.desa_by_ttn_id
            LEFT OUTER JOIN manager m ON m.id = hd.manager_id
            {query_start_date}
            GROUP BY hd.code, d.id, dt.group, m.name, rpl.code)
            SELECT s.*,
            CASE
                WHEN sudah_diukur >= jumlah_bidang THEN 'ORDER UKUR SELESAI'
                ELSE 'ORDER UKUR BELUM SELESAI'
            END AS status
            FROM subquery s
            ORDER BY nomor_request ASC
    """

    db_session = db.session
    response = await db_session.execute(query)
    result = response.all()

    x = 5
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
    
    total_order_selesai = RoundTwo(sum([data[6] for data in result if data[15] == "ORDER UKUR SELESAI"])/10000)
    total_order_belum_selesai = RoundTwo(sum([data[6] for data in result if data[15] == "ORDER UKUR BELUM SELESAI"])/10000)

    ws.cell(row=x + 3, column=2, value=f"TOTAL ORDER SELESAI: {total_order_selesai} Ha")
    ws.merge_cells(start_row=x + 3, start_column=2, end_row=x + 3, end_column=end_column)
    ws.cell(row=x + 4, column=2, value=f"TOTAL ORDER BELUM SELESAI: {total_order_belum_selesai} Ha")
    ws.merge_cells(start_row=x + 4, start_column=2, end_row=x + 4, end_column=end_column)

    
    ws.cell(row=x + 6, column=2, value="CATATAN:")
    ws.merge_cells(start_row=x + 6, start_column=2, end_row=x + 6, end_column=end_column)
    ws.cell(row=x + 7, column=2, value="1. ORDER UKUR SELESAI JIKA SUDAH JADI PETA LOKASI")
    ws.merge_cells(start_row=x + 7, start_column=2, end_row=x + 7, end_column=end_column)
    ws.cell(row=x + 8, column=2, value="2. JIKA BIDANG SUDAH DIUKUR, NAMUN BELUM JADI PETA LOKASI MAKA MASIH MENJADI OUTSTANDING ORDER UKUR")
    ws.merge_cells(start_row=x + 8, start_column=2, end_row=x + 8, end_column=end_column)
    
    

    excel_data = BytesIO()

    # Simpan workbook ke objek BytesIO
    wb.save(excel_data)

    # Set posisi objek BytesIO ke awal
    excel_data.seek(0)
    

    return StreamingResponse(excel_data,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                             headers={"Content-Disposition": "attachment; filename=generated_excel.xlsx"})