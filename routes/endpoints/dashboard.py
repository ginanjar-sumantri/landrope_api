from fastapi import APIRouter, Depends
from fastapi_async_sqlalchemy import db
from sqlmodel import text, select
from schemas.dashboard_sch import OutStandingSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, create_response)

router = APIRouter()

@router.get("/search", response_model=GetResponseBaseSch[list[OutStandingSch]])
async def dashboard_outstanding():

    """Get for search"""

    db_session = db.session

    query = text(f"""
            with subquery as (select 
            b.id,
            b.id_bidang,
            b.alashak,
            tr.id as kjb_termin_id,
            hd.satuan_bayar,
            hd.satuan_harga,
            tr.nilai,
            'DP' as jenis_bayar
            from hasil_peta_lokasi hpl
            inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
            inner join kjb_harga hg ON hg.kjb_hd_id = dt.kjb_hd_id and hg.jenis_alashak = dt.jenis_alashak
            inner join kjb_termin tr ON hg.id = tr.kjb_harga_id and tr.jenis_bayar = 'DP'
            inner join kjb_hd hd ON hd.id = hg.kjb_hd_id
            inner join bidang b ON b.id = hpl.bidang_id 
            left outer join spk s ON s.bidang_id = hpl.bidang_id and s.jenis_bayar = 'DP'
            Where s.id is null
            and (select count(*) from checklist_kelengkapan_dokumen_hd c_hd
                inner join checklist_kelengkapan_dokumen_dt c_dt ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id 
                and c_dt.jenis_bayar = 'DP'
                inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
                Where c_hd.bidang_id = hpl.bidang_id
                and b_dt.file_path is null
                ) <= 0
            and (select count(*) 
                from spk ss 
                where ss.jenis_bayar = 'LUNAS' 
                and ss.is_void != True 
                and ss.bidang_id = hpl.bidang_id) <= 0
            UNION
            select 
            b.id,
            b.id_bidang,
            b.alashak,
            tr.id as kjb_termin_id,
            hd.satuan_bayar,
            hd.satuan_harga,
            tr.nilai,
            'PELUNASAN' as jenis_bayar
            from hasil_peta_lokasi hpl
            inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
            inner join kjb_harga hg ON hg.kjb_hd_id = dt.kjb_hd_id and hg.jenis_alashak = dt.jenis_alashak
            inner join kjb_termin tr ON hg.id = tr.kjb_harga_id and tr.jenis_bayar = 'PELUNASAN'
            inner join kjb_hd hd ON hd.id = hg.kjb_hd_id
            inner join bidang b ON b.id = hpl.bidang_id 
            left outer join spk s ON s.bidang_id = hpl.bidang_id and s.jenis_bayar = 'PELUNASAN'
            Where s.id is null
            and (select count(*) from checklist_kelengkapan_dokumen_hd c_hd
                inner join checklist_kelengkapan_dokumen_dt c_dt ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id 
                and c_dt.jenis_bayar = 'PELUNASAN'
                inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
                Where c_hd.bidang_id = hpl.bidang_id
                and b_dt.file_path is null
                ) <= 0
            and (select count(*) 
                from spk ss 
                where ss.jenis_bayar = 'LUNAS' 
                and ss.is_void != True 
                and ss.bidang_id = hpl.bidang_id) <= 0
            UNION
            select 
            b.id,
            b.id_bidang,
            b.alashak,
            null as kjb_termin_id,
            null as satuan_bayar,
            null as satuan_harga,
            null as nilai,
            'PENGEMBALIAN_BEBAN_PENJUAL' as jenis_bayar 
            from hasil_peta_lokasi hpl
            inner join bidang b ON b.id = hpl.bidang_id
            left outer join spk s ON s.bidang_id = hpl.bidang_id and s.jenis_bayar = 'PENGEMBALIAN_BEBAN_PENJUAL'
            Where (select count(*) 
                from bidang_komponen_biaya kb
                left outer join invoice_detail inv_dt ON inv_dt.bidang_komponen_biaya_id = kb.id
                left outer join invoice inv ON inv.id = inv_dt.invoice_id
                left outer join termin tr ON tr.id = inv.termin_id
                where kb.is_void != true and kb.is_retur = true
                and tr.id is null and tr.jenis_bayar = 'PENGEMBALIAN_BEBAN_PENJUAL'
                ) > 0
            and (select count(*) from checklist_kelengkapan_dokumen_hd c_hd
                inner join checklist_kelengkapan_dokumen_dt c_dt ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id 
                and c_dt.jenis_bayar = 'BIAYA_LAIN'
                inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
                Where c_hd.bidang_id = hpl.bidang_id
                and b_dt.file_path is null
                ) <= 0
            UNION
            select 
            b.id,
            b.id_bidang,
            b.alashak,
            null as kjb_termin_id,
            null as satuan_bayar,
            null as satuan_harga,
            null as nilai,
            'PAJAK' as jenis_bayar
            from hasil_peta_lokasi hpl
            inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
            inner join bidang b ON b.id = hpl.bidang_id 
            left outer join spk s ON s.bidang_id = hpl.bidang_id and s.jenis_bayar = 'PAJAK'
            Where s.id is null
            and (select count(*) from checklist_kelengkapan_dokumen_hd c_hd
                inner join checklist_kelengkapan_dokumen_dt c_dt ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id 
                and c_dt.jenis_bayar = 'BIAYA_LAIN'
                inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
                Where c_hd.bidang_id = hpl.bidang_id
                and b_dt.file_path is null
                ) <= 0
            Order by id_bidang)
            select 'outstanding_spk' as tipe_worklist, Count(*) as total from subquery
            union
            select 'outstanding_hasil_peta_lokasi' as tipe_worklist, count(*) as total 
            from request_peta_lokasi
            where kjb_dt_id not in (select kjb_dt_id from hasil_peta_lokasi)
            union
            select 'outstanding_invoice' as tipe_worklist, count(*) as total 
            from spk
            inner join workflow ON spk.id = workflow.reference_id
            where spk.id not in (select spk_id 
                            from invoice i
                            join termin t on t.id = i.termin_id
                            where i.is_void != true 
                            and t.jenis_bayar not in ('UTJ', 'UTJ_KHUSUS', 'BEGINNING_BALANCE'))
            and jenis_bayar not in ('PAJAK', 'BEGINNING_BALANCE')
            and is_void != True
            and workflow.last_status = 'COMPLETE'
            union
            SELECT 'outstanding_payment' as tipe_worklist, count(*)
            FROM invoice i
            WHERE i.amount - ((
                CASE
                WHEN i.use_utj = True THEN (
                    SELECT COALESCE(SUM(amount), 0)
                    FROM invoice i_utj
                    Inner join termin tr on tr.id = i_utj.termin_id
                    WHERE i.bidang_id = i_utj.bidang_id
                    and tr.jenis_bayar in ('UTJ', 'UTJ_KHUSUS')
                )
                ELSE 0
                END
            ) + (
                select coalesce(sum(amount), 0) 
                from payment_detail py
                where i.id = py.invoice_id
                and py.is_void != true
                ) + (
                    Select 
                        Coalesce(SUM(idt.amount), 0)
                        from invoice_detail idt
                        inner join bidang_komponen_biaya kb on kb.id = idt.bidang_komponen_biaya_id
                        inner join beban_biaya bb on bb.id = kb.beban_biaya_id
                        inner join bidang b on b.id = kb.bidang_id
                        where idt.invoice_id = i.id
                        and kb.beban_pembeli = false)
                            ) != 0 and i.is_void != TRUE
        """)

    result = await db_session.execute(query)
    data = result.fetchall()
    return create_response(data=data)