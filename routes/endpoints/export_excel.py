from fastapi import FastAPI, HTTPException, APIRouter, Response
from fastapi.responses import StreamingResponse
from schemas.tahap_detail_sch import TahapDetailForPrintOut, TahapDetailForExcel
from schemas.bidang_overlap_sch import BidangOverlapForPrintout
from schemas.bidang_sch import BidangAllPembayaran
from services.helper_service import BundleHelper
from common.enum import StatusSKEnum, HasilAnalisaPetaLokasiEnum
import pandas as pd
import crud
from io import BytesIO
from typing import List
from pydantic import BaseModel
from services.pdf_service import PdfService
from services.adobe_service import PDFToExcelService
from uuid import UUID
from datetime import datetime

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
        html_content += f"<th>{payment_type['jenis_bayar']} {payment_type['tanggal']}</th>"
    html_content += "</tr>"

    for rumah in data_rumah_list:
        html_content += f"<tr><td rowspan='{len(rumah.kepemilikan) + 1 if len(rumah.kepemilikan) == 0 else len(rumah.kepemilikan)}'>{rumah.id}</td><td rowspan='{len(rumah.kepemilikan) + 1 if len(rumah.kepemilikan) == 0 else len(rumah.kepemilikan)}'>{rumah.luas}</td><td rowspan='{len(rumah.kepemilikan) + 1 if len(rumah.kepemilikan) == 0 else len(rumah.kepemilikan)}'>{rumah.harga}</td>"
        
        # Menambahkan data Kepemilikan
        for i, kepemilikan in enumerate(rumah.kepemilikan):
            if i == 0:
                html_content += f"<td>{kepemilikan.nama}</td><td>{kepemilikan.tahun}</td>"
                # Menambahkan data Pembayaran
                if rumah.pembayaran:
                    for payment_type in all_payment_types:
                        matching_payment = next((p for p in rumah.pembayaran if p.jenis_pembayaran == payment_type['jenis_bayar'] and p.tanggal_pembayaran == payment_type['tanggal']), None)
                        if matching_payment:
                            html_content += f"<td rowspan='{len(rumah.kepemilikan) + 1 if len(rumah.kepemilikan) == 0 else len(rumah.kepemilikan)}'>{matching_payment.jumlah}</td>"
                        else:
                            html_content += f"<td rowspan='{len(rumah.kepemilikan) + 1 if len(rumah.kepemilikan) == 0 else len(rumah.kepemilikan)}'>-</td>"
                else:
                    for payment_type in all_payment_types:
                        html_content += f"<td rowspan='{len(rumah.kepemilikan) + 1 if len(rumah.kepemilikan) == 0 else len(rumah.kepemilikan)}'>-</td>"
                html_content += "</tr>"
            else:
                html_content += f"<tr><td>{kepemilikan.nama}</td><td>{kepemilikan.tahun}</td></tr>"

    html_content += "</table></body></html>"

    try:
        doc = await PdfService().get_pdf(html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    response = Response(doc, media_type='application/pdf')
    response.headers["Content-Disposition"] = f"attachment; filename=test.pdf"
    return response

bulan_dict = {
    "January": "Januari",
    "February": "Februari",
    "March": "Maret",
    "April": "April",
    "May": "Mei",
    "June": "Juni",
    "July": "Juli",
    "August": "Agustus",
    "September": "September",
    "October": "Oktober",
    "November": "November",
    "December": "Desember"
}

@router.get("export/excel/bidang")
async def bidang_excel(id:UUID):

    termin = await crud.termin.get_by_id(id=id)

    date_obj = datetime.strptime(str(termin.tanggal_rencana_transaksi), "%Y-%m-%d")
    nama_bulan_inggris = date_obj.strftime('%B')  # Mendapatkan nama bulan dalam bahasa Inggris
    nama_bulan_indonesia = bulan_dict.get(nama_bulan_inggris, nama_bulan_inggris)  # Mengonversi ke bahasa Indonesia
    tanggal_hasil = date_obj.strftime(f'%d {nama_bulan_indonesia} %Y')

    obj_bidangs = await crud.tahap_detail.get_multi_by_tahap_id_for_printout(tahap_id=termin.tahap_id)

    bidangs:list[TahapDetailForExcel] = []
    nomor_urut_bidang = []
    overlap_exists = False
    no = 1
    for bd in obj_bidangs:
        bidang = TahapDetailForExcel(**dict(bd),
                                    no=no,
                                    total_hargaExt="{:,.0f}".format(bd.total_harga),
                                    harga_transaksiExt = "{:,.0f}".format(bd.harga_transaksi),
                                    luas_suratExt = "{:,.0f}".format(bd.luas_surat),
                                    luas_nettExt = "{:,.0f}".format(bd.luas_nett),
                                    luas_ukurExt = "{:,.0f}".format(bd.luas_ukur),
                                    luas_gu_peroranganExt = "{:,.0f}".format(bd.luas_gu_perorangan),
                                    luas_pbt_peroranganExt = "{:,.0f}".format(bd.luas_pbt_perorangan),
                                    luas_bayarExt = "{:,.0f}".format(bd.luas_bayar),
                                    is_bold=False)
        

        overlaps = await crud.bidangoverlap.get_multi_by_bidang_id_for_printout(bidang_id=bd.bidang_id)
        list_overlap = []
        for ov in overlaps:
            overlap = BidangOverlapForPrintout(**dict(ov))
            bidang_utama = await crud.bidang.get_by_id(id=bd.bidang_id)
            if (bidang_utama.status_sk == StatusSKEnum.Sudah_Il and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap) or (bidang_utama.status_sk == StatusSKEnum.Belum_IL and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear):
                overlap.nib = await BundleHelper().get_key_value(dokumen_name="NIB PERORANGAN", bidang_id=bidang_utama.id)

            list_overlap.append(overlap)

        bidang.overlaps = list_overlap

        if len(bidang.overlaps) > 0:
            overlap_exists = True

        pembayarans = await crud.bidang.get_all_pembayaran_by_bidang_id(bidang_id=bidang.bidang_id)
        bidang.pembayarans = pembayarans

        bidangs.append(bidang)
        no = no + 1
    
    html_content = await generate_html_content(list_tahap_detail=bidangs, overlap_exists=overlap_exists, tanggal=tanggal_hasil)

    try:
        doc = await PdfService().get_pdf(html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate pdf document")
    
    
    excel = await PDFToExcelService().export_pdf_to_excel(data=doc)
    
    
    return StreamingResponse(excel, 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=memo_pembayaran.xlsx"})
    
    

async def generate_html_content(list_tahap_detail:list[TahapDetailForExcel], overlap_exists:bool|None = False, tanggal:str|None = '') -> str | None:
    html_content = "<html><body>"
    html_content = """<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="pdfkit-page-size" content="Legal" />
    <meta name="pdfkit-orientation" content="Landscape" />
    <title>Memo Tanah Overlap</title>
    <style>
      @page {
        size: A3 landscape;
      }

      body {
        margin: 0;
        font-family: Arial, sans-serif;
      }
      </style>
      </head>"""
    html_content += """<table border='1'>"""
    html_content += f"""
    <tr>
    <td>No</td><td>:</td><td></td>
    </tr>
    <tr>
    <td>Tanggal</td><td>:</td><td>{tanggal}</td>
    </tr>
    """
    
    if overlap_exists:
        html_content += """
        <tr>
        <th colspan='10' style='background-color: white; border-left: none; border-top: none'></th>
        <th align='center' colspan='10'>OVERLAP DAMAI</td>
        <th
            style='
              background-color: white;
              border-right: none;
              border-top: none;
            '
            colspan='2'
          ></th>
        </tr>
        """

    html_content +="""
        <tr>  
        <th>NO</th>
        <th>ID BID</th>
        <th>ALIAS</th>
        <th>PEMILIK</th>
        <th>SURAT ASAL</th>
        <th>L SURAT</th>
        <th>L UKUR</th>
        <th>L NETT</th>
        <th>L BAYAR</th>
        <th>NO PETA</th>"""
    
    if overlap_exists:
          html_content += """ 
          <th>KET</th>
          <th>NAMA</th>
          <th>ALASHAK</th>
          <th>THP</th>
          <th>LUAS</th>
          <th>L.O</th>
          <th>KAT</th>
          <th>NO NIB</th>
          <th>ID BID</th>
          <th>STATUS</th>"""

    html_content += """
          <th>HARGA</th>
          <th>JUMLAH</th>"""
    
    # Menambahkan kolom pembayaran
    all_payment_types = []
    for bidang in list_tahap_detail:
        for pembayaran in bidang.pembayarans:
            exists = next((types for types in all_payment_types if types['name'] == pembayaran.name and types['id_pembayaran'] == pembayaran.id_pembayaran), None)
            if exists:
                continue
            all_payment_types.append({'name':pembayaran.name, 'id_pembayaran':pembayaran.id_pembayaran})
    for payment_type in all_payment_types:
        html_content += f"<th>{payment_type['name'].replace('_', ' ')}</th>"
    html_content += "</tr>"

    for bidang in list_tahap_detail:
        html_content += f"""<tr>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.no}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.id_bidang}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.group}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.pemilik_name}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.alashak}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_suratExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_ukurExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_nettExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_bayarExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.no_peta}</td>
        """
        if len(bidang.overlaps) > 0:
        # Menambahkan data overlap
            for i, overlap in enumerate(bidang.overlaps):
                if i == 0:
                    html_content += f"""
                                    <td>{overlap.ket}</td>
                                    <td>{overlap.nama}</td>
                                    <td>{overlap.alashak}</td>
                                    <td></td>
                                    <td>{overlap.luasExt}</td>
                                    <td>{overlap.luas_overlapExt}</td>
                                    <td>{overlap.kat}</td>
                                    <td>{overlap.nib or ''}</td>
                                    <td>{overlap.id_bidang}</td>
                                    <td>{overlap.status_overlap}</td>
                                    <td rowspan='{len(bidang.overlaps)}'>{bidang.harga_transaksiExt}</td>
                                    <td rowspan='{len(bidang.overlaps)}'>{bidang.total_hargaExt}</td>
                                    """
                    # Menambahkan data Pembayaran
                    if bidang.pembayarans:
                        for payment_type in all_payment_types:
                            matching_payment = next((p for p in bidang.pembayarans if p.name == payment_type['name'] and p.id_pembayaran == payment_type['id_pembayaran']), None)
                            if matching_payment:
                                amount_bayar = "{:,.0f}".format(matching_payment.amount)
                                html_content += f"<td rowspan='{len(bidang.overlaps)}'>{amount_bayar}</td>"
                            else:
                                html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
                    else:
                        for payment_type in all_payment_types:
                            html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
                    html_content += "</tr>"
                else:
                    html_content += f"""<tr>
                                    <td>{overlap.ket}</td>
                                    <td>{overlap.nama}</td>
                                    <td>{overlap.alashak}</td>
                                    <td></td>
                                    <td>{overlap.luasExt}</td>
                                    <td>{overlap.luas_overlapExt}</td>
                                    <td>{overlap.kat}</td>
                                    <td>{overlap.nib or ''}</td>
                                    <td>{overlap.id_bidang}</td>
                                    <td>{overlap.status_overlap}</td></tr>"""
        else:
            if overlap_exists:
                html_content += f"""<td align="center">-</td>
                                    <td align='center'>-</td>
                                    <td align='center'>-</td>
                                    <td align='center'>-</td>
                                    <td align='center'>-</td>
                                    <td align='right'>-</td>
                                    <td align='right'>-</td>
                                    <td align='right'>-</td>
                                    <td align='right'>-</td>
                                    <td align='center'>-</td>"""
            
            html_content += f"""<td align='right'>{ bidang.harga_transaksiExt or '' }</td>
                                <td align='right'>{ bidang.total_hargaExt or '' }</td>"""
            
            # Menambahkan data Pembayaran
            if bidang.pembayarans:
                for payment_type in all_payment_types:
                    matching_payment = next((p for p in bidang.pembayarans if p.name == payment_type['name'] and p.id_pembayaran == payment_type['id_pembayaran']), None)
                    if matching_payment:
                        amount_bayar = "{:,.0f}".format(matching_payment.amount)
                        html_content += f"<td rowspan='{len(bidang.overlaps)}'>{amount_bayar}</td>"
                    else:
                        html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
            else:
                for payment_type in all_payment_types:
                    html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
            html_content += "</tr>"
    
    total_luas_surat = "{:,.0f}".format(sum([b.luas_surat for b in list_tahap_detail]))
    total_luas_ukur = "{:,.0f}".format(sum([b.luas_ukur for b in list_tahap_detail]))
    total_luas_nett = "{:,.0f}".format(sum([b.luas_nett for b in list_tahap_detail]))
    total_luas_bayar = "{:,.0f}".format(sum([b.luas_bayar for b in list_tahap_detail]))
    total_harga = "{:,.0f}".format(sum([b.total_harga for b in list_tahap_detail]))

    html_content += f"""<tr>
                    <td></td>
                    <td colspan='4'>Sub Total</td>
                    <td>{total_luas_surat}</td>
                    <td>{total_luas_ukur}</td>
                    <td>{total_luas_nett}</td>
                    <td>{total_luas_bayar}</td>
                """
    if overlap_exists:
        total_luas_surat_ov = "{:,.0f}".format(sum([ov.luas for b in list_tahap_detail for ov in b.overlaps]))
        total_luas_ov = "{:,.0f}".format(sum([ov.luas_overlap for b in list_tahap_detail for ov in b.overlaps]))
        html_content += f"""
                <td colspan='5'></td>
                <td>{total_luas_surat_ov}</td>
                <td>{total_luas_ov}</td>
                <td colspan='5'></td>
                """
    else:
        html_content += f"""
                <td colspan='2'></td>
                """
    html_content += f"""<td>{total_harga}</td>"""

    # Menambahkan total data Pembayaran
    
    for payment_type in all_payment_types:
        total_pembayaran = "{:,.0f}".format(sum([p.amount for b in list_tahap_detail for p in b.pembayarans if p.name == payment_type['name'] and p.id_pembayaran == payment_type['id_pembayaran']]))
        
        html_content += f"""<td>{total_pembayaran}</td>"""

    html_content += "</tr>"

    html_content += "</table></body></html>"

    return html_content



